from bs4 import BeautifulSoup
import time
import requests
from typing import List
import csv
from sys import argv

def get_money_amount(money_string):
    return int(money_string.split("$")[1].replace(" ", ""))



class Film_Detailed:
    def __init__(self, title: str, year: int, award_amount: int, box_office: int | None, budget: int | None, time_mins: int | None, reviews: List[int]):
        self.title = title
        self.year = year
        self.award_amount = award_amount
        self.box_office = box_office
        self.budget = budget
        self.time_mins = time_mins
        self.reviews = reviews


def save_detailed_films_to_csv(films: List[Film_Detailed], filename: str, new_file: bool):
    headers = ["Title", "Year", "Award Amount", "Box Office", "Budget", "Time (mins)", "Reviews"]
    if (new_file):
        mode = "w"
    else:
        mode = "a"

    with open(filename, mode=mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)

        if (new_file):
            writer.writerow(headers)

        for film in films:
            if (film.box_office is None):
                box_office = "-"
            else:
                box_office = film.box_office

            if (film.budget is None):
                budget = "-"
            else:
                budget = film.budget

            if(film.time_mins is None):
                time = "-"
            else:
                time = film.time_mins
            writer.writerow([
                film.title,
                film.year,
                film.award_amount,
                box_office,
                budget,
                time,
                f'"{",".join(map(str, film.reviews))}"'
            ])


class Film:
    def __init__(self, title: str, year: int, award_amount: int, box_office: int | None, budget: int | None, time_mins: int, score_avg: int):
        self.title = title
        self.year = year
        self.award_amount = award_amount
        self.box_office = box_office
        self.budget = budget
        self.time_mins = time_mins
        self.score_avg = score_avg


def save_films_to_csv(films: List[Film], filename: str, new_file: bool):
    headers = ["Title", "Year", "Award Amount", "Box Office", "Budget", "Time (mins)", "Score"]
    if (new_file):
        mode = "w"
    else:
        mode = "a"

    with open(filename, mode=mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)

        if (new_file):
            writer.writerow(headers)

        for film in films:

            if (film.box_office is None):
                box_office = "-"
            else:
                box_office = film.box_office

            if (film.budget is None):
                budget = "-"
            else:
                budget = film.budget
                
            if(film.time_mins is None):
                time = "-"
            else:
                time = film.time_mins
                
            writer.writerow([
                film.title,
                film.year,
                film.award_amount,
                box_office,
                budget,
                time,
                film.score_avg
            ])


base_url = "https://www.filmweb.pl"


def url_films_on_page(pageNum):
    return base_url + "/films/search?page=" + str(pageNum)


films_detailed = []
films = []
max_page = 1000
if (len(argv) > 1):
    if (argv[1]):
        page = int(argv[1])
        film_count = (page-1)*10
    else:
        if (len(argv) > 2):
            max_page = int(argv[2])
        page = 1
        film_count = 1
    if ("--file-created" in argv):
        created_films_csv = True
    else:
        created_films_csv = False
else:
    page = 1
    film_count = 1



while page <= max_page:
    print(f"Page: {page}")

    start = time.time()
    film_list_response = requests.get(url_films_on_page(page))
    film_list_html = BeautifulSoup(film_list_response.text)
    film_list_element = film_list_html.select_one('.searchApp__results.previewHolder.hasBorder.isSmall.hasRatings.hasBadge.showGenres.showCast.showExtra.showOriginalTitle')
    if (film_list_element):
        film_links = film_list_element.select(".preview__link")
        for link in film_links:
            film_page_response = requests.get(base_url + link["href"])
            response_html = BeautifulSoup(film_page_response.text)
            title = response_html.select_one(".filmCoverSection__title").text
            print(f"Film nr {film_count}: {title}")
            year = int(response_html.select_one(".filmCoverSection__year").text)
            if(year > 2024):
                continue
            runtime_el = response_html.select_one(".filmCoverSectino__duration")
            if(runtime_el):
                runtime = runtime_el.text
                if ("h" in runtime):
                    hours = int(runtime.split("h")[0])
                else:
                    hours = 0

                if ("m" in runtime):
                    minutes = int(runtime.split(" ")[-1].split("m")[0])
                else:
                    minutes = 0
                runtime_mins = hours*60+minutes
            else:
                runtime_mins = None
            runtime = response_html.select_one(".filmCoverSection__duration").text


            genre = response_html.find("span", class_="linkButton__label", itemprop="genre").text
            
            boxoffice_all = response_html.select_one("span.filmInfo__info.filmInfo__info--column")
            if (boxoffice_all):
                boxoffice_world_els = [box_el for box_el in boxoffice_all.children if "na świecie" in box_el.text]
                if (len(boxoffice_world_els) > 0):
                    boxoffice_gross_el = boxoffice_world_els[0]
                    boxoffice_gross = get_money_amount(boxoffice_gross_el.text.split("na świecie")[0])
                else:
                    boxoffice_usa_els = [box_el for box_el in boxoffice_all.children if "w USA" in box_el.text]
                    if (len(boxoffice_usa_els) > 0):
                        boxoffice_usa_el = boxoffice_usa_els[0]
                        boxoffice_gross = get_money_amount(boxoffice_usa_el.text.split("w USA")[0])
                    else:
                        boxoffice_gross = None
            else:
                boxoffice_gross = None
            
            budget_element = response_html.find("span", string="budżet")
            if (budget_element):
                sibling = budget_element.find_next_sibling("span", class_='filmInfo__info')
                budget_el = sibling.select_one("span")
                budget = get_money_amount(budget_el.text)
            else:
                budget = None

            awards_element = response_html.select_one("a.awardsSection__link")
            if (awards_element):
                awards_link = awards_element["href"]
                awards_response = requests.get(base_url + awards_link)
                awards_html = BeautifulSoup(awards_response.text)
                award_amount = int(awards_html.select_one("span.page__headerCounter").text)
            else:
                award_amount = 0

            if (page == 1):
                # reviews
                film_reviews = []
                forum_page = 1
                forum_response = requests.get(base_url + link["href"] + "/discussion?page=" + str(forum_page))
                forum_html = BeautifulSoup(forum_response.text)
                pagination_elements = forum_html.select("ul.pagination__list")
                pagination_element = pagination_elements[-1]
                #print("pagination element")
                #print(pagination_element)
                pagination_buttons = [
                    li for li in pagination_element.find_all('li', class_='pagination__item')
                    if 'pagination__item--next' not in li.get('class', [])
                ]
                pages_amount = int(pagination_buttons[-1].select_one("a").text)
                print(f"Visiting {pages_amount} forum pages...")
                while (forum_page <= pages_amount):
                    print(f"forum page: {forum_page}")
                    topics_list = forum_html.select_one("div.forumTopicsList__items")
                    for forum_topic in topics_list.findChildren("div", recursive=False):
                        topic_review = forum_topic.select_one("span.forumTopic__starsNo")
                        if (topic_review):
                            review = int(topic_review.text)
                            film_reviews.append(review)
                    forum_page += 1
                    forum_response = requests.get(base_url + link["href"] + "/discussion?page=" + str(forum_page))
                    forum_html = BeautifulSoup(forum_response.text)
                films_detailed.append(Film_Detailed(title, year, award_amount, boxoffice_gross, budget, runtime_mins, film_reviews))
            else:
                score_el = response_html.select_one("div.filmRating.filmRating--filmRate.filmRating--hasPanel")
                if(score_el):
                    score = float(response_html.select_one("div.filmRating.filmRating--filmRate.filmRating--hasPanel")["data-rate"])
                    films.append(Film(title, year, award_amount, boxoffice_gross, budget, runtime_mins, score))
                else:
                    continue
            film_count += 1

    end = time.time()
    print(f"Page {page} finished, took {end-start} s")
    if (page == 1):
        print("Saving detailed films to csv!")
        save_detailed_films_to_csv(films_detailed, "./films_detailed.csv", True)
    elif (page % 10 == 0):
        print("Saving films to csv!")
        save_films_to_csv(films, "./films.csv", not created_films_csv)
        created_films_csv = True
        films = []
    page += 1


