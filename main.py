from abc import ABC, abstractmethod
import pickle
from collections import UserDict
from datetime import datetime, timedelta
from pathlib import Path

file_path = Path("database.bin")

class View(ABC):
    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_all(self, book):
        pass

    @abstractmethod
    def show_birthdays(self, birthdays):
        pass

class ConsoleView(View):
    def show_message(self, message):
        print(message)

    def show_all(self, book):
        if not book.data:
            print("kniga pusta")
        else:
            for record in book.data.values():
                print(record)

    def show_birthdays(self, birthdays):
        if not birthdays:
            print("Нет ближайших дней рождения!!!")
        else:
            for day in birthdays:
                print(f"{day['name']}: {day['congratulation_date']}")





class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if len(value) == 10 and value.isdigit():
            self.__value = value
        else:
            raise ValueError("Invalid phone format")


class Birthday(Field):
    def __init__(self, value):
        date_format = "%d.%m.%Y"
        try:
            self.date = datetime.strptime(value, date_format).date()
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        self.phones = [p for p in self.phones if str(p) != phone_number]

    def edit_phone(self, old_number, new_number):
        for phone in self.phones:
            if str(phone) == old_number:
                phone.value = new_number
                return
        raise ValueError("Phone number not found")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    @staticmethod
    def find_next_weekday(d, weekday):
        """
        Функція для знаходження наступного заданого дня тижня після заданої дати.
        d: datetime.date - початкова дата.
        weekday: int - день тижня від 0 (понеділок) до 6 (неділя).
        """
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Якщо день народження вже минув у цьому тижні.
            days_ahead += 7
        return d + timedelta(days_ahead)

    def get_upcoming_birthdays(self, days=7) -> list:
        today = datetime.today().date()
        upcoming_birthdays = []

        for user in self.data.values():
            if user.birthday is None:
                continue
            birthday_this_year = user.birthday.date.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            if 0 <= (birthday_this_year - today).days <= days:
                if birthday_this_year.weekday() >= 5:  # субота або неділя
                    birthday_this_year = self.find_next_weekday(
                        birthday_this_year, 0
                    )  # Понеділок

                congratulation_date_str = birthday_this_year.strftime("%Y.%m.%d")
                upcoming_birthdays.append(
                    {
                        "name": user.name.value,
                        "congratulation_date": congratulation_date_str,
                    }
                )

        return upcoming_birthdays


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Name not found. Please, check and try again."
        except ValueError as e:
            return e  # "Incorrect value. Please check and try again."
        except IndexError:
            return "Enter correct information."

    return inner


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Contact updated."
    else:
        raise KeyError


@input_error
def show_phone(args, book):
    (name,) = args
    record = book.find(name)
    if record:
        return "; ".join([str(phone) for phone in record.phones])
    else:
        raise KeyError


def show_all(book):
    return "\n".join([str(record) for record in book.data.values()])


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_birthday(args, book):
    name = args[0]
    birthday = args[1]
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    else:
        raise KeyError


@input_error
def show_birthday(args, book):
    (name,) = args
    record = book.find(name)
    return str(record.birthday)


def load_data():
    if file_path.is_file():
        with open(file_path, "rb") as file:
            return pickle.load(file)
    else:
        return AddressBook()


def main():
    book = load_data()
    view = ConsoleView()


    

    view.show_message("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            view.show_message("Good bye")
            with open(file_path, "wb") as file:
                pickle.dump(book, file)
            break

        elif command == "hello":
            view.show_message("How can I help you?")

        elif command == "add":
            result = add_contact(args, book)
            view.show_message(result)

        elif command == "change":
            result = change_contact(args, book)
            view.show_message(result)

        elif command == "phone":
            result = show_phone(args, book)
            view.show_message(result)

        elif command == "all":
            view.show_all(book)

        elif command == "add-birthday":
            result = add_birthday(args, book)
            view.show_message(result)

        elif command == "show-birthday":
            result = show_birthday(args, book)
            view.show_message(result)

        elif command == "birthdays":
            birthdays = book.get_upcoming_birthdays()
            view.show_birthdays(birthdays)
        

if __name__ == "__main__":  
    main() 