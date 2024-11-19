#!/usr/bin/env python3
import sys
import os
import argparse
import csv
import tomllib
import tomli_w

from pathlib import Path
from dotenv import load_dotenv
from gradescope_api.client import GradescopeClient
from piazza_api import Piazza

settings_path = Path("settings.toml")

def read_piazza_roster(csv_path):
    roster = {}
    with open(csv_path, newline="") as handle:
        roster_reader = csv.reader(handle)
        header=next(roster_reader)
        for entry in roster_reader:
            if entry[2] == "Student":
                name = entry[0].split(",")
                if len(name) == 1:
                    pz_name = name[0]
                elif len(name) == 2:
                    pz_name = f"{name[1].strip()} {name[0].strip()}"
                else:
                    pz_name = f"{name[1].strip()} {name[0].strip()}"
                email = entry[1]
                roster[pz_name.lower()] = email
    return roster

def make_course_entry(identifier, gs_id, roster, course_path=Path("courses")):
    settings = tomllib.loads(settings_path.read_text())
    if identifier in settings["courses"]:
        print(f"WARNING: Course with identifier \"{identifier}\" already exists, overwriting")
    else:
        settings["courses"].append(identifier)
    course_dir = Path(course_path)
    course_dir.mkdir(exist_ok=True)
    
    cfg_path = Path(f"{course_path}/{identifier}.toml")
    cfg = {
        "gradescope-id" : gs_id,
        "roster" : roster
    }
    cfg_path.write_text(tomli_w.dumps(cfg))
    
    if "default-course" not in settings:
        print(f"No default course set, setting to {identifier}.")
        settings["default-course"] = identifier
    elif settings["default-to-newest"]:
        print(f"Setting {identifier} to the default course.")
        settings["default-course"] = identifier
    settings_path.write_text(tomli_w.dumps(settings))


def initialize_settings():
    if settings_path.exists():
        return
    print("Settings file not found, initializing to defaults.")
    default_settings = {
        "course_path" : "courses",
        "courses" : [],
        "default-to-newest" : True
        "default-length" : 5
    }
    settings_path.write_text(tomli_w.dumps(default_settings))

def yes_no_helper():
    option = None
    while option is None:
        option = input("(y/N): ").lower()
        if len(option) == 0 or option[0] == "n":
            option = False
        elif option[0] == "y":
            option = True
        else:
            option = None
    return option

def interactive_setup():
    load_dotenv()
    settings = tomllib.loads(settings_path.read_text())

    print("Connecting to gradescope...\n")
    gs_client = GradescopeClient(email=os.environ["GS_EMAIL"], password=os.environ["GS_PASSWORD"])
    gs_courses = gs_client.get_courses()
    
    print("Enter the number (i) of the course to use for configuring:")
    longest_name_len = max(map(lambda x: len(x.get_name()), gs_courses))
    for ix,course in enumerate(gs_courses):
        course_name = course.get_name() 
        print(f"  ({ix+1}) {course_name:<{longest_name_len}}\t{course.get_term()}\t{course.course_id}")
        
    ix = None
    while ix is None:
        ix = input("Selection: ")
        if ix.isdigit():
            ix = int(ix)-1
            if ix < 0 or ix >= len(gs_courses):
                print(f"{ix+1} not within range, enter a number (i) corresponding to the desired course")
                ix = None
        else:
            ix = None
    gs_course = gs_courses[ix]

    print("\nDo you have csv of the roster?\nYou can obtain one by Manage Class->Enroll Students->Download Roster as CSV, \notherwise this will connect to piazza and try to build a roster that way.")
    have_csv = yes_no_helper()

    if have_csv:
        roster_path = Path(input("Enter path to roster csv: "))
        while not roster_path.exists():
            roster_path = Path(input("Path not found, try again: "))
        roster = read_piazza_roster(roster_path)
    else:
        print("\nConnecting to piazza...")
        pz_client = Piazza()
        pz_client.user_login(email=os.environ["PZ_EMAIL"], password=os.environ["PZ_PASSWORD"])
        pz_courses = [x for x in filter(lambda x: x["is_ta"], pz_client.get_user_classes())]
        print("Enter the number (i) of the piazza course to use:")
        longest_name_len = max(map(lambda x: len(x["num"]), pz_courses))
        for ix,course in enumerate(pz_courses):
            course_name = course["num"]
            course_term = course["term"]
            print(f"  ({ix+1}) {course_name:<{longest_name_len}}\t{course_term}")
        
        ix = None
        while ix is None:
            ix = input("Selection: ")
            if ix.isdigit():
                ix = int(ix)-1
                if ix < 0 or ix >= len(pz_courses):
                    print(f"{ix+1} not within range, enter a number (i) corresponding to the desired course")
                    ix = None
            else:
                ix = None
        pz_course = pz_client.network(pz_courses[ix]["nid"])
        students = filter(lambda x: x["role"] == "student", pz_course.get_all_users())
        valid_emails = set(gs_student.email for gs_student in gs_course.get_roster())
        roster = {}
        sans_emails = []
        for student in students:
            name = student["name"]
            emails = student["email"].split(", ")
            valid_email = None
            for email in emails:
                if email in valid_emails:
                    valid_email = email
                    break
            if valid_email is None:
                sans_emails.append(name)
                # probably implement a check to see if that student even is enrolled in gradescope
            else:
                roster[name] = email
        if sans_emails:
            print(f"Warning: could not find an email for the following students. Check to make sure they aren't enrolled on gradescope\n  {'\n  '.join(sans_emails)}")
    
    identifier = None
    while identifier is None:
        identifier = input("\nEnter an identifier to use for this course, no spaces:\n").strip()
        if len(identifier) == 0 or " " in identifier:
            identifier = None
            continue
        if identifier in settings["courses"]:
            print(f"Course with identifier \"{identifier}\" already exists, do you want to overwrite it?")
            if not yes_no_helper():
                identifier = None
    make_course_entry(identifier, gs_course.course_id, roster)

def main():
    initialize_settings()

    if len(sys.argv) == 1:
        interactive_setup()
        exit(0)

    def config_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument("-id", "--id", help="Identifier to use")
        parser.add_argument("-r", "--roster", type=Path, help="Path to roster csv exported from piazza")
        parser.add_argument("-g", "--gradescope", help="Gradescope course id")
        parser.add_argument("-l", "--list", action="store_true", help="list possible options for gradescope ids")
        # parser.add_argument("-d", "--set-default")
        return parser

    parser = config_parser()
    cfg_args = parser.parse_args()
    if cfg_args.list:
        load_dotenv()
        gs_client = GradescopeClient(email=os.environ["GS_EMAIL"], password=os.environ["GS_PASSWORD"])
        gs_courses = gs_client.get_courses()
        longest_name_len = max(map(lambda x: len(x.get_name()), gs_courses))
        print(f"ID\tcourse Name{' '*(max(0,longest_name_len-11))}\tTerm")
        for ix,course in enumerate(gs_courses):
            course_name = course.get_name()
            print(f"{course.course_id}\t{course_name:<{longest_name_len}}\t{course.get_term()}")
        exit(0)
    make_course_entry(cfg_args.id, cfg_args.gradescope, read_piazza_roster(cfg_args.roster))

if __name__ == "__main__":
    main()
