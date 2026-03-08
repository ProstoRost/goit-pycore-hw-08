import pickle
from collections import UserDict
from datetime import datetime, date, timedelta


# ===== БАЗОВІ КЛАСИ ПОЛІВ =====

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not self._is_valid_phone(value):
            raise ValueError("Phone number must have exactly 10 digits")
        super().__init__(value)

    def _is_valid_phone(self, value):
        digits = "".join(ch for ch in value if ch.isdigit())
        return len(digits) == 10


class Birthday(Field):
    def __init__(self, value):
        try:
            birthday_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(birthday_date)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


# ===== КОНТАКТ ТА АДРЕСНА КНИГА =====

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_value):
        phone = Phone(phone_value)
        self.phones.append(phone)

    def remove_phone(self, phone_value):
        for phone in self.phones:
            if phone.value == phone_value:
                self.phones.remove(phone)
                return True
        return False

    def edit_phone(self, old_phone, new_phone):
        for phone in self.phones:
            if phone.value == old_phone:
                new_phone_obj = Phone(new_phone)
                phone.value = new_phone_obj.value
                return True
        return False

    def find_phone(self, phone_value):
        for phone in self.phones:
            if phone.value == phone_value:
                return phone
        return None

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "no phones"
        bd_str = str(self.birthday) if self.birthday else "no birthday"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {bd_str}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        if name in self.data:
            return self.data[name]
        return None

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return True
        return False

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            bd_date = record.birthday.value
            birthday_this_year = bd_date.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            delta = birthday_this_year - today
            days_diff = delta.days

            if 0 <= days_diff <= 7:
                congratulation_date = birthday_this_year
                weekday = congratulation_date.weekday()

                if weekday == 5:  # субота
                    congratulation_date = congratulation_date + timedelta(days=2)
                elif weekday == 6:  # неділя
                    congratulation_date = congratulation_date + timedelta(days=1)

                upcoming.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": congratulation_date,
                    }
                )

        return upcoming


# ===== СЕРІАЛІЗАЦІЯ / ДЕСЕРІАЛІЗАЦІЯ З PICKLE =====

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# ===== ДЕКОРАТОР ДЛЯ ОБРОБКИ ПОМИЛОК =====

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            if e.args:
                return str(e)
            return "Invalid value."
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the argument for the command."
    return inner


# ===== ПАРСЕР КОМАНД =====

def parse_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return "", []
    parts = user_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args


# ===== ОБРОБНИКИ КОМАНД =====

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
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError("No such contact")
    changed = record.edit_phone(old_phone, new_phone)
    if changed:
        return "Phone number changed."
    return "Old phone not found."


@input_error
def show_phones(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError("No such contact")
    if not record.phones:
        return "No phones for this contact."
    phones_str = ", ".join(phone.value for phone in record.phones)
    return f"{name}: {phones_str}"


@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "Address book is empty."
    lines = []
    for record in book.data.values():
        lines.append(str(record))
    return "\n".join(lines)


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday_str, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError("No such contact")
    record.add_birthday(birthday_str)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError("No such contact")
    if record.birthday is None:
        return "Birthday is not set for this contact."
    return f"{name}: {record.birthday}"


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."

    grouped = {}
    for item in upcoming:
        date_str = item["congratulation_date"].strftime("%d.%m.%Y")
        name = item["name"]
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(name)

    lines = []
    for date_str, names in sorted(grouped.items()):
        names_str = ", ".join(names)
        lines.append(f"{date_str}: {names_str}")

    return "\nBirthdays next week:\n" + "\n".join(lines)


# ===== ГОЛОВНА ФУНКЦІЯ БОТА =====

def main():
    # 1. При запуску намагаємося завантажити книгу з файлу
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            # 2. Перед виходом зберігаємо книгу на диск
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phones(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "":
            print("Enter the argument for the command")
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()