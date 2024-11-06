import pandas as pd
import random
from random import randint
from datetime import date, timedelta

members = pd.read_csv('members.txt')

f = open('Rental_History.txt', 'w')
f.write('Bicycle ID,Rental Date,Return Date,Member ID\n')

# #add the errors in
# error_missing = random.sample(range(0,200), 20) #missing value
# error_format = random.sample(range(0,200), 20) #return date BEFORE rental date
# error_date = random.sample(range(0,200), 20) #a date in the future

for line in range(0,200):
    #select random bike
    bike_id = randint(1,200)

    #select random date between now and 1 jan 2021
    date = date.today() - timedelta(days=randint(1,1388))

    #select return date two weeks after
    return_date = date + timedelta(days=randint(3,21))

    #select random member id
    member_id = random.choice( members['MemberID'].to_list() )

    # if line in error_missing:
    #     #missing values
    #     f.write(f'{bike_id},{date},{return_date},missing\n')
    
    # elif line in error_format:
    #     #return date BEFORE rental date
    #     f.write(f'{bike_id},{date},{date - timedelta(days=randint(1,14))},{member_id}\n')
    
    # elif line in error_date:
    #     #invalid date
    #     f.write(f'{bike_id},{date},2026-13-01,{member_id}\n')

    # else:
        #write in delimted format to file
    f.write(f'{bike_id},{date},{return_date},{member_id}\n')

