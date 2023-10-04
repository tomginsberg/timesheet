import calendar
import datetime
import json
import os
import subprocess
import sys

import fire
import iterfzf


def custom_exception_hook(exctype, value, traceback):
    """
    A function to customize the exception handling.

    Parameters:
    - exctype: The type of the exception.
    - value: The value associated with the exception.
    - traceback: The traceback information for the exception.

    Returns:
    - None
    """
    red_color = "\033[91m"
    reset_color = "\033[0m"
    print(f"{red_color}{value}{reset_color}")


sys.excepthook = custom_exception_hook


def select_date():
    """
    Lets the user select a date using iterfzf.
    It finds all the timesheet root directories and converts the numerical months into words.
    The user can then fuzzy search for a particular date, and the original name of the directory is returned.
    """
    # List all directories in the current working directory
    all_items = os.listdir()
    date_directories = [item for item in all_items if os.path.isdir(item) and is_valid_date_dir(item)]

    # Convert numerical months to words and create a mapping
    date_mapping = {}
    for date_dir in date_directories:
        year, month, day = date_dir.split('-')
        month_name = calendar.month_name[int(month)]
        formatted_date = f"{day} {month_name} {year}"
        date_mapping[formatted_date] = date_dir

    # Let the user select a date using iterfzf
    selected_date = iterfzf.iterfzf(date_mapping.keys())
    if not selected_date:
        print("No date selected.")
        return None

    # Return the original directory name
    return date_mapping[selected_date]


def is_valid_date_dir(directory: str):
    """
    Checks if the given directory name matches the date pattern (YYYY-MM-DD).
    :param directory: Name of the directory.
    :return: True if it matches the date pattern, False otherwise.
    """
    import re
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', directory))


def create_project_entry(date_str, project):
    formatted_name = project.replace(' ', '_')
    while True:
        hours = input(f"🕒 How many hours did you spend on {project}? ")
        try:
            hours = float(hours)
            break
        except ValueError:
            print("Invalid input for hours. Please enter a number.")
            continue
    notes_file = os.path.join(date_str, f"{formatted_name}-notes.txt")
    with open(notes_file, 'w') as f:
        f.write(f'Notes for project: {project}\n')
    subprocess.run(['vim', notes_file])
    media_folder = None
    if input("Do you have any additional media to attach? (y/n): ").lower() == 'y':
        media_folder = os.path.join(date_str, f"{formatted_name}-media")
        os.makedirs(media_folder)
        input(
            f"🎥 Press Enter once you have copied all the media you want to attach to {os.path.realpath(media_folder)}")
    entry = {
        'name': project,
        'notes': notes_file,
        'media': media_folder,
        'hours': hours
    }
    return entry


class Timesheet:

    @staticmethod
    def add_project(name: str):
        """
        Adds a new project to projects.json
        :param name: project name
        If projects.json does not exist or the name is already in the list create it
        """
        if not os.path.exists('projects.json'):
            json.dump([name], open('projects.json', 'w'))
        else:
            projects = Timesheet.list_projects()
            if name in projects:
                print(f"Project {name} already exists.")
                return
            projects.append(name)
            with open('projects.json', 'w') as f:
                json.dump(projects, f)
        print(f"✅ Project {name} has been added.")

    @staticmethod
    def delete_project(name: str):
        """
        Deletes a project from projects.json
        :param name: project name to be deleted
        """
        projects = Timesheet.list_projects()
        if name not in projects:
            print(f"Project {name} does not exist.")
            return
        projects.remove(name)
        with open('projects.json', 'w') as f:
            json.dump(projects, f)
        print(f"❌ Project {name} has been deleted.")

    @staticmethod
    def list_projects():
        """
        Returns a list of current projects
        """
        if not os.path.exists('projects.json'):
            raise FileNotFoundError("There is no projects.json file in this directory. Please use timesheet setup")
        with open('projects.json', 'r') as f:
            return json.load(f)

    @staticmethod
    def create():
        """
        Creates a new timesheet for a specific date.

        This function prompts the user to select a date from a list of options: 'today', 'yesterday', or 'earlier'.
        If 'today' is selected, the current date is used. If 'yesterday' is selected, the previous date is used.
        If 'earlier' is selected, the user is prompted to enter a date in the format 'YYYY-MM-DD'.

        If the selected date already has a timesheet directory, a FileExistsError is raised. Otherwise, a new
        directory is created with the name of the selected date.

        The function then prompts the user to select a project from a list of available projects. For each selected
        project, the user is prompted to enter the number of hours worked on the project. The project details are
        stored in a list.

        After all projects are entered, the user is prompted to confirm the total number of hours worked on the
        selected date. The timesheet is then created as a dictionary object containing the date, the list of
        projects, and the total hours worked.

        The timesheet is saved in a JSON file named 'timesheet.json' within the newly created directory.

        Finally, a summary of the entered information is displayed by calling the 'show' method of the 'Timesheet'
        class.

        :return: None
        """
        options = ['today', 'yesterday', 'earlier']
        opt = iterfzf.iterfzf(options)

        if opt == 'today':
            date_str = datetime.date.today().strftime('%Y-%m-%d')
        elif opt == 'yesterday':
            date_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        elif opt == 'earlier':
            # Let the user enter a date
            date_str = input("Enter a date (YYYY-MM-DD): ")
            # check if the date is valid
            assert is_valid_date_dir(date_str), "Invalid date"
        else:
            print("No date selected.")
            return

        if os.path.exists(date_str):
            raise FileExistsError(f"A directory with the name {date_str} already exists."
                                  f"Use timesheet edit instead")
        os.makedirs(date_str)

        projects_list = Timesheet.list_projects()
        total_hours = 0
        projects_details = []

        while True:
            used_projects = [entry['name'] for entry in projects_details]
            project = iterfzf.iterfzf(set(projects_list) - set(used_projects))
            if not project:
                print("Invalid project selected.")
                continue

            entry = create_project_entry(date_str, project)
            total_hours += entry['hours']

            projects_details.append(entry)

            if input("❔ Did you work on more projects today? (y/n): ").lower() != 'y':
                break

        while True:
            total_input_hours = input(f"⌛ Please confirm the total number of hours worked today (>= {total_hours}): ")
            if total_input_hours == '':
                break
            try:
                if float(total_input_hours) < total_hours:
                    print('The total number of hours worked cannot be less '
                          'than the total number of hours worked today.')
                    continue
                total_hours = float(total_input_hours)
                break
            except ValueError:
                print("Invalid input for total hours.")

        timesheet = {
            'date': date_str,
            'projects': projects_details,
            'hours': total_hours
        }

        with open(os.path.join(date_str, 'timesheet.json'), 'w') as f:
            json.dump(timesheet, f)
        print('✅ Timesheet created.')
        print("\nSummary of the entered information:\n")
        Timesheet.show(date_str)

    @staticmethod
    def show(date: str = None):
        """
        Prints a timesheet summary nicely given the path to a timesheet root directory.
        It includes the notes and paths of media.
        :param date: Path to the timesheet root directory.
        """
        if date is None:
            directory = select_date()
        else:
            directory = date
        timesheet_file = os.path.join(directory, 'timesheet.json')
        if not os.path.exists(timesheet_file):
            print(f"No timesheet found in the directory {directory}")
            return

        with open(timesheet_file, 'r') as f:
            timesheet = json.load(f)

        print(f"Date: {timesheet['date']}")
        print(f"Total Hours Worked: {timesheet['hours']}")
        print("Projects:")

        for project in timesheet['projects']:
            print(f"  - Project Name: {project['name']}")
            print(f"    Hours: {project['hours']}")

            notes_file = project['notes']
            if os.path.exists(notes_file):
                print("    Notes:")
                with open(notes_file, 'r') as f:
                    for line in f.readlines():
                        print(f"      {line.strip()}")
            else:
                print("    Notes: [File not found]")

            media_folder = project['media']
            if media_folder and os.path.exists(media_folder):
                print("    Media:")
                for media in os.listdir(media_folder):
                    print(f"      {os.path.join(media_folder, media)}")
            else:
                print("    Media: [Media not found]")

        print("\n")

    @staticmethod
    def open(date: str = None):
        """
        Opens a file or directory using the default application associated with the operating system.

        Args:
            date (str, optional): The date to open. If not provided, a date will be selected using the select_date function.

        Raises:
            ValueError: If the operating system is not supported.

        Returns:
            None
        """
        if date is None:
            date = select_date()  # Assuming you have a function called select_date

        if sys.platform == "darwin":  # macOS
            cmd = ['open', date]
        elif sys.platform == "linux" or sys.platform == "linux2":  # Linux
            cmd = ['xdg-open', date]
        elif sys.platform == "win32":  # Windows
            cmd = ['start', date]
        else:
            raise ValueError("Unsupported operating system")

        subprocess.run(cmd)

    @staticmethod
    def edit(date: str = None):
        """
        Edits a timesheet entry.

        Parameters:
            date (str, optional): The date of the timesheet entry. If not provided, the user will be prompted to select
            a date. Defaults to None.

        Returns:
            None
        """
        # Let the user select a timesheet directory

        if date is None:
            selected_directory = select_date()
        else:
            selected_directory = date

        timesheet_file = os.path.join(selected_directory, 'timesheet.json')
        if not os.path.exists(timesheet_file):
            print(f"No timesheet found in the directory {selected_directory}")
            return

        with open(timesheet_file, 'r') as f:
            timesheet = json.load(f)

        while True:
            # Let the user select a project or "New Project Entry"
            project_names = [project['name'] for project in timesheet['projects']]
            project_names.append("New Project Entry")
            selected_project_name = iterfzf.iterfzf(project_names)
            if not selected_project_name:
                print("No project selected.")
                return

            if selected_project_name == "New Project Entry":
                # Handle new project entry (similar to the create method)
                # Get the list of projects from projects.json that are not already in this timesheet
                available_projects = set(Timesheet.list_projects()) - set(project_names[:-1])
                new_project_name = iterfzf.iterfzf(list(available_projects))
                if not new_project_name:
                    print("No project selected.")
                    return

                # ... (rest of the steps similar to the create method) ...
                # After collecting all the details, append the new project to the timesheet['projects'] list
                timesheet['projects'].append(create_project_entry(selected_directory, new_project_name))
                total_hours = timesheet['hours']
                while True:
                    total_input_hours = input(
                        f"Please confirm the total number of hours worked on {selected_directory} ({total_hours}): ")
                    if total_input_hours == '':
                        break
                    try:
                        total_hours = float(total_input_hours)
                        break
                    except ValueError:
                        print("Invalid input for total hours.")
                timesheet['hours'] = total_hours

            else:
                # Let the user select what they want to edit or if they want to delete the project
                selected_option = iterfzf.iterfzf(['hours', 'notes', 'media', 'delete'])
                if not selected_option:
                    print("No option selected.")
                    return

                # Find the selected project in the timesheet
                selected_project = next(
                    (project for project in timesheet['projects'] if project['name'] == selected_project_name), None)
                if not selected_project:
                    print(f"Project {selected_project_name} not found in the timesheet.")
                    return

                if selected_option == 'hours':
                    # Handle editing hours
                    while True:
                        new_hours = input(f"Enter the new number of hours for {selected_project_name}: ")
                        try:
                            selected_project['hours'] = float(new_hours)
                            break
                        except ValueError:
                            print("Invalid input for hours. Please enter a number.")
                elif selected_option == 'notes':
                    # Handle editing notes
                    subprocess.run(['vim', selected_project['notes']])
                elif selected_option == 'media':
                    # Handle editing media
                    if not os.path.exists(selected_project['media']):
                        os.makedirs(selected_project['media'])

                    input(
                        f"Press Enter once you have copied all the media you want to attach to "
                        f"{selected_project['media']}.")
                elif selected_option == 'delete':
                    # Handle deleting the project
                    if os.path.exists(selected_project['notes']):
                        os.remove(selected_project['notes'])
                    if selected_project['media'] and os.path.exists(selected_project['media']):
                        import shutil
                        shutil.rmtree(selected_project['media'])
                    timesheet['projects'].remove(selected_project)

            # Save the updated timesheet back to the file
            with open(timesheet_file, 'w') as f:
                json.dump(timesheet, f)
            print("Timesheet has been updated.")


def main():
    fire.Fire(Timesheet)


if __name__ == '__main__':
    main()
