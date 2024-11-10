import pandas as pd
import random
from random import randint
from datetime import date, timedelta

members = pd.read_csv('members.txt')

f = open('Rental_History.txt', 'w')
f.write('Bicycle ID,Rental Date,Return Date,Member ID\n')

# #add the errors in
error_missing = random.sample(range(0,200), 10) #missing value
error_format = random.sample(range(0,200), 20) #return date BEFORE rental date
error_date = random.sample(range(0,200), 10) #a date that can't exist

for line in range(0,500):
    #generate variables
    bike_id = randint(1,200)
    rent_date = date.today() - timedelta(days=randint(1,1388))
    return_date = rent_date + timedelta(days=randint(3,21))
    member_id = random.choice( members['MemberID'].to_list() )

    #add errors and populate file
    if line in error_missing:
        #missing values
        f.write(f'{bike_id},{rent_date},missing,{member_id}\n')
    
    if line in error_format:
        #return date BEFORE rental date
        f.write(f'{bike_id},{rent_date},{rent_date - timedelta(days=randint(1,14))},{member_id}\n')
    
    elif line in error_date:
        #invalid date
        f.write(f'{bike_id},{rent_date},2026-130-01,{member_id}\n')

    else:
        #write in delimted format to file
        f.write(f'{bike_id},{rent_date},{return_date},{member_id}\n')

