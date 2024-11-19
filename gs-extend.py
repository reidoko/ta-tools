#!/usr/bin/env python3
import os
import argparse
import csv
import tomllib

from dotenv import load_dotenv
from pathlib import Path

from gradescope_api.client import GradescopeClient
from gradescope_api.course import GradescopeCourse


settings_path = Path("settings.toml")
settings = tomllib.loads(settings_path.read_text())
if len(settings["courses"]) == 0:
    print("No courses found, make sure you run ./gs-config.py first!")
    exit(0)

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--id", choices=settings["courses"], default=settings["default-course"], help="Course identifier")
parser.add_argument("names", nargs="*", help="student names")
parser.add_argument("-d", "--days", type=int, default=settings["default-length"], help="Number of days after deadline to extend the assignment. Does not stack with other extensions.")
parser.add_argument("-s", "--string", help="String for assignment titles to contain (e.g. -s hw4 to apply extension to all assignments with 'hw4' in the title)")

args = parser.parse_args()
course_info_path = Path(f"{settings['course_path']}/{args.id}.toml")
course_info = tomllib.loads(course_info_path.read_text())
roster = course_info["roster"]
exit(0)

client = GradescopeClient(email=os.environ["GS_EMAIL"], password=os.environ["GS_PASSWORD"])
course = client.get_course(course_id=course_info['gradescope-id'])
assignments = list(map(lambda x: course.get_assignment(assignment_id=x), current_ass))

for raw_name in args.names:
    student_name = raw_name.lower()
    if student_name not in roster:
        print(f"Could not find {student_name} in the roster")
        # TODO: try to find a reasonable match in the roster?
        continue
    else:
        email = roster[student_name]
    print(student_name, email)
    for assignment in assignments:
        assignment.apply_extension(roster[student_name], args.days)
