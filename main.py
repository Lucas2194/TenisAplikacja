import pandas as pd
import json
from datetime import datetime, timedelta
import os

df_csv = pd.read_csv('23.03-30.03.csv', skipinitialspace = True)

df_csv['start_time'] = pd.to_datetime(df_csv['start_time'], format = '%d.%m.%Y %H:%M')
df_csv['end_time'] = pd.to_datetime(df_csv['end_time'], format='%d.%m.%Y %H:%M')

# print(df_csv)

with open('23.03-30.03.json', encoding='utf-8') as f:
    data = json.load(f)

dfs = []

for date, appointments in data.items():
    df = pd.DataFrame(appointments)
    df['date'] = date
    dfs.append(df)

df_final_json = pd.concat(dfs, ignore_index=True)

df_final_json['date'] = df_final_json['date'].apply(lambda x: x + ".2023")
df_final_json['start_time'] = pd.to_datetime(df_final_json['date'] + ' ' + df_final_json['start_time'])
df_final_json['end_time'] = pd.to_datetime(df_final_json['date'] + ' ' + df_final_json['end_time'])

df_final_json = df_final_json.drop(columns=["date"])

df_final_json = df_final_json[["name", "start_time", "end_time"]]

while True:
    choice = input("Please choose a file you want to use: 'csv' or 'json'. ")
    if choice == 'csv':
        df_final = df_csv
        break
    elif choice == 'json':
        df_final = df_final_json
        break
    else:
        print("You have chosen an invalid option. Please try again ")

# print(df_final)

def makeReservation():
    global df_final
    name = input("What's your Name? ")

    while True:
        reservation_date_str = input("When would you like to book? {DD.MM.YYYY HH:MM} ")
        try:
            reservation_date = datetime.strptime(reservation_date_str, '%d.%m.%Y %H:%M')
        except ValueError:
            print("Invalid date format. Please enter the date and time in the format DD.MM.YYYY HH:MM")
            continue

        # Check if reservation date is at least one hour in the future
        if reservation_date <= datetime.now() + timedelta(hours=1):
            print("Reservation can't be made less than one hour from now.")
            return

        # Check if user has more than 2 reservations this week
        user_reservations = df_final[df_final['name'] == name]
        week_number = reservation_date.isocalendar()[1]
        if len(user_reservations[user_reservations['start_time'].dt.isocalendar().week == week_number]) >= 2:
            print("User already has 2 reservations this week.")
            return

        break

    # Ask for reservation duration (30, 60, or 90 minutes)
    available_durations = [30, 60, 90]
    print("Available reservation durations: ", available_durations)
    while True:
        requested_duration = input("How long would you like to reserve the court for? ")
        try:
            requested_duration = int(requested_duration)
        except ValueError:
            print("Invalid duration. Please choose from the available options.")
            continue
        if requested_duration not in available_durations:
            print("Invalid duration. Please choose from the available options.")
        else:
            break

    # Check if the requested duration is available at the specified time
    end_time = reservation_date + timedelta(minutes=requested_duration)
    overlapping_reservations = df_final[(df_final['start_time'] < end_time) & (df_final['end_time'] > reservation_date)]
    while not overlapping_reservations.empty:
        print(
            f"The court is already reserved for the requested duration from {overlapping_reservations['start_time'].iloc[0]} to {overlapping_reservations['end_time'].iloc[0]}")
        shorter_duration = max(d for d in available_durations if d < requested_duration)
        if shorter_duration:
            print(f"Would you like to book for {shorter_duration} minutes instead?")
            response = input("Enter Y for Yes, N for No: ")
            if response.upper() == 'Y':
                requested_duration = shorter_duration
                end_time = reservation_date + timedelta(minutes=requested_duration)
                overlapping_reservations = df_final[
                    (df_final['start_time'] < end_time) & (df_final['end_time'] > reservation_date)]
            else:
                print("Reservation not made.")
                return
        else:
            print("Reservation not made.")
            return

    # Add reservation to DataFrame
    new_reservation = pd.DataFrame({'name': [name], 'start_time': [reservation_date], 'end_time': [end_time]})
    df_final = pd.concat([df_final, new_reservation], ignore_index=True)
    df_final.sort_values(by='start_time', inplace=True)

    print("Reservation added successfully!")

def cancelReservation():
    global df_final
    name = input("What's your Name? ")

    while True:
        cancel_date_str = input("What is the date of the reservation you want to cancel? {DD.MM.YYYY HH:MM} ")
        try:
            cancel_date = datetime.strptime(cancel_date_str, '%d.%m.%Y %H:%M')
        except ValueError:
            print("Invalid date format. Please enter the date in the following format: {DD.MM.YYYY HH:MM}")
            continue

        # Check if reservation date is at least one hour in the future
        if cancel_date <= datetime.now() + timedelta(hours=1):
            print("Reservation can't be cancelled less than one hour from now.")
            return

        # Check if there is a reservation for this user on specified date
        matching_reservations = df_final[(df_final['name'] == name) & (df_final['start_time'].dt.date == cancel_date.date())]
        if len(matching_reservations) == 0:
            print("No reservation found for this user on specified date.")
            break
        else:
            # Remove the matching reservation from the DataFrame
            df_final = df_final[~((df_final['name'] == name) & (df_final['start_time'].dt.date == cancel_date.date()))]
            print("Reservation cancelled successfully!")
            break

def print_schedule():
    global df_final
    while True:
        try:
            start_date_str = input("Enter start date {DD.MM.YYYY}: ")
            start_date = datetime.strptime(start_date_str, '%d.%m.%Y')
            end_date_str = input("Enter end date {DD.MM.YYYY}: ")
            end_date = datetime.strptime(end_date_str, '%d.%m.%Y')
            break
        except ValueError:
            print("Invalid date format. Please enter the date in the following format: {DD.MM.YYYY}")

    delta = timedelta(days=1)
    current_date = start_date
    while current_date <= end_date:
        print(current_date.strftime("\n%A:\n"), end="")
        daily_reservations = df_final[(df_final['start_time'].dt.date == current_date.date())]
        if daily_reservations.empty:
            print("No Reservations\n")
        else:
            for _, row in daily_reservations.iterrows():
                print(f"* {row['name']} {row['start_time'].strftime('%d.%m.%Y %H:%M')} - {row['end_time'].strftime('%d.%m.%Y %H:%M')}")
            print("")
        current_date += delta

def saveSchedule():
    global df_final
    while True:
        try:
            start_date_str = input("Enter start date (DD.MM.YYYY): ")
            end_date_str = input("Enter end date (DD.MM.YYYY): ")
            file_format = input("Enter file format (csv or json): ")
            file_name = input("Enter file name: ")

            start_date = datetime.strptime(start_date_str, '%d.%m.%Y')

            # Check if end date is greater than the maximum date in the dataframe
            max_date = df_final['end_time'].max()
            if pd.isna(max_date):
                end_date = start_date
            elif datetime.strptime(end_date_str, '%d.%m.%Y') > max_date:
                end_date = max_date
            else:
                end_date = datetime.strptime(end_date_str, '%d.%m.%Y')

            # Filter schedule between start and end dates
            df_filtered = df_final[
                (df_final['start_time'].dt.date >= start_date.date()) & (df_final['end_time'].dt.date <= end_date.date())]

            if file_format == 'csv':
                file_path = f"{file_name}.csv"
                df_filtered.to_csv(file_path, index=False)
                print(f"Schedule saved to {file_path}")
            elif file_format == 'json':
                file_path = f"{file_name}.json"
                schedule_dict = {}
                for date in pd.date_range(start=start_date, end=end_date):
                    date_str = date.strftime('%d.%m.%Y')
                    date_schedule = df_filtered[df_filtered['start_time'].dt.date == date.date()]
                    date_schedule = date_schedule.apply(
                        lambda x: {"name": x["name"], "start_time": x["start_time"].strftime('%H:%M'),
                                   "end_time": x["end_time"].strftime('%H:%M')}, axis=1)
                    date_schedule = date_schedule.tolist()
                    schedule_dict[date_str] = date_schedule
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(schedule_dict, f, ensure_ascii=False, indent=4)
                print(f"Schedule saved to {file_path}")
            else:
                print("Invalid file format")

            # If everything is successful, break out of the loop
            break
        except ValueError:
            print("Invalid date format. Please enter dates in the following format: DD.MM.YYYY")
        except FileNotFoundError:
            print("File path not found.")

    # saveSchedule()

def main_menu():
    while True:
        print('What would you like to do: ')
        print('1. Make a reservation')
        print('2. Cancel a reservation')
        print('3. Print schedule')
        print('4. Save schedule to a file')
        print('5. Exit')

        choice = input('Choose option: ')

        if choice == '1':
            makeReservation()
        elif choice == '2':
            cancelReservation()
        elif choice == '3':
            print_schedule()
        elif choice == '4':
            saveSchedule()
        elif choice == '5':
            print('See You!')
            break
        else:
            print('Wrong input!')

if __name__ == '__main__':
    main_menu()