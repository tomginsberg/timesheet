# timesheet

## Install
Make sure `vim` is installed on your system

Install the package using
```shell
pip install git+https://github.com/tomginsberg/timesheet.git
```

*Note this project uses python dependencies `fire` and `iterfzf` which will automatically be installed*

## Usage
Create your timesheet directory
```shell
mkdir "~/MyTimesheets"
cd "MyTimesheets"
```
Set up your database and add projects
```shell
timesheet add-project 'hamiltonian simulation'
timesheet add-project 'error correction'
```
Create your first timesheet!
```shell
timesheet create
```
### More commands
View an existing timesheet (uses an interactive selector)
```shell
timesheet show
```
Edit an existing timesheet (uses an interactive selector)
```shell
timesheet edit
```
Delete a project (will not delete entries from time sheets)
```shell
timesheet delete-project 'project name'
```
Open a timesheet in your system viewer (uses an interactive selector)
```shell
timesheet open
```