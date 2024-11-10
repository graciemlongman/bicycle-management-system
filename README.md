# README
### PLEASE RUN MENU.IPYNB IN JUPYTER LAB. THE TEXTBOXES DO NOT WORK IN NOTEBOOK.

### Note: database was initialised before submission so no need to do so in the notebook.

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
|**data\generateRental_History.py**| A program which generates the rental histroy data|
|----|----|
| **database.db** | SQLite database holding information regarding inventory and rental history|
| **data\Rental_History.txt** | Text file to be loaded into the SQLite database |
| **data\Bicycle_info.txt** | Text file to be loaded into the SQLite database |
| **members.txt** | Text file holding memberhsip information |
|----|----|
| **bike_images** | Folder containing .jpg images which are then loaded into the database.|

# Data and Database Structure
### Database normalisation
The database is normalised to 3NF. It contains four tables, `bicycle_inventory`, `bicycle_models`, `rental_hist` and `images`

    +-------------------+        +---------------------+        +---------------------+
    | bicycle_inventory |        |    bicycle_models   |        |        images       |
    +-------------------+        +---------------------+        +---------------------+
    | id (PK)           |◄───────| model_id (PK)       |◄───────| brand (PK)          |
    | model_id (FK)     |        | brand (FK)          |        | photo               |
    | purchase_date     |        | type                |        +---------------------+
    | condition         |        | size                |
    | status            |        | daily_rental_rate   |
    +-------------------+        | weekly_rental_rate  |
             ▲                   | cost                |
             │                   | instore             |
             │                   +---------------------+
    +-------------------+
    |    rental_hist    |
    +-------------------+
    | log (PK)          |
    | id (FK)           |
    | rental_date       |
    | return_date       |
    | member_id         |
    +-------------------+

### Error Handling:
 Errors were populated into both the `Bicycle_info.txt`:
 1. Incorrect date format
 2. Invalid currency format i.e., 15£ instead of 15/day
 3. Missing in `brand` col (brand was imputed based on daily rental price)

 and `Rental_History.txt`:
 1. Invalid rental date (just delete entry)
 2. Return date before rental date (swap dates back over)
 3. Missing dates (just delete entry)


# Graphical User Interface Functionality 
- The `Search` button requires the user to use the dropdown widgets to search by brand type or size. This displays a pd.DataFrame.

- The `Rent` button requires the user to input their member ID, bicycle ID, rental date (using a widget.DatePicker), and the number of days they would like to rent for. 
    - This returns a dataframe and confirmation message. Incorrect inputs (e.g., blank date) will display error messages to the user in red.
- The `Return` button requires the user to input their bicycle ID, return date (using a widget.DatePicker) and the bicycle condition.
    - This returns a HTML confirmation message displaying the price of charges, where if late/damage charges are applicable they will be displayed in red. Damage charges incur if the condition is marked as 'damaged'
- The `Select` button allows the user to user sliders to choose a budget and decide how it should be allocated - either towards maintaining inventory or expanding.
    - This returns a dataframe of recommended bikes and the corresponding images below.
- The `Visualise` button displays a heatmap of rental frequency, by member ID and each unique bike model. It also displays the model_ID key below the plot. 
