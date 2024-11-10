# README

A Bicycle Rental Mangement System.

See all python files and their descriptions below.

| File | Description |
| ----- | ----- |
| **menu.ipynb** | A jupyter notebook which serves as the main program, based on a Graphical User Interface using IPyWidgets. |
| **bikeSearch.py** | Module containing the `BikeSearch` class, which handles functions related to searching for bicycles according to brand, type and frame size. |
| **bikeRent.py** | Module containing the `BikeRent` class, which handles functions related to renting bicycles. |
| **bikeReturn.py** | Module containing the `BikeReturn` class, which handles functions related to returning bicycles. |
| **bikeSelect.py** | Module containing the `BikeSelect` class, which handles functions related to recommending bicycles. |
| **database.py** | Module containing the `Database` class, which handles functions related to database handling, such as initialisation. |
|**membershipManager.pyc**| Module containing functions to deal with memberships|
|**generateRentals.py**| A program which generates the rental histroy data|
|----|----|
| **database.db** | SQLite database holding information regarding inventory and rental history|
| **Rental_History.txt** | Text file to be loaded into the SQLite database |
| **Bicycle_info.txt** | Text file to be loaded into the SQLite database |
| **members.txt** | Text file holding memberhsip information |


# Data and Database Structure
### Database normalisation
The database is normalised to 3NF. Put in a database diagram

### Error Handling
 Errors were populated into both the `Bicycle_info.txt`:
 1. Incorrect date format 
 2. Invalid currency format 
 3. Missing in `brand` col (infer brand using daily rental price)


 and `Rental_History.txt`:
 1. Invalid rental date (just delete entry)
 2. Return date before rental date (swap dates back over)
 3. Missing dates (just delete entry)