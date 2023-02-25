### Navigation Contents ###
# navigation_sidebar = soup.find("nav", id="mw-panel-toc")
# navigation_contents_list = soup.find("ul", id="mw-panel-toc-list")
# navigation_contents = navigation_contents_list.find_all("div", class_="vector-toc-text"})

# def parse_page_to_json(soup):
def parse_page_paragraphs(soup):
    
    paragraphs = []
    
    page = {}
    
    ##!! is this what I did in WAeasy
    title = soup.find(id="firstHeading").text
    page['Title'] = title ##!! is this good naming??
    print(f"Title: {title}")
    
    body_content = soup.find("div", id="bodyContent")
    ##!! look for categories, etc.
    
    # focusing on the main part of the body for now
    body_content = body_content.find("div", class_="mw-parser-output")

    short_description = body_content.find("div", class_="shortdescription nomobile noexcerpt noprint searchaux")
    if short_description is not None:
        short_description = short_description.text
        print(f"Short description: {short_description}")
    print("\n")
    
    # infobox = body_content.find("table", class_="infobox")
    # if is+infobox:
    #     page['Infobox'] = parse_infobox(infobox)
    
    h2 = "Lead Section" # section title
    h3, h4, h5, h6 = "", "", "", "" # titles of subsections
    
    for element in body_content.contents:
        if element.name in ["p", "h2", "h3", "h4", "h5", "h6"]:
            if element.name == "h2":
                # new section
                h2 = element.find("span", class_="mw-headline").text
                h3, h4, h5, h6 = "", "", "", ""
            elif element.name == "h3":
                h3 = element.find("span", class_="mw-headline").text
                h4, h5, h6 = "", "", ""
            elif element.name == "h4":
                h3 = element.find("span", class_="mw-headline").text
                h5, h6 = "", ""
            elif element.name == "h5":
                h3 = element.find("span", class_="mw-headline").text
                h6 = ""
            elif element.name == "h6":
                h3 = element.find("span", class_="mw-headline").text
            else:
                paragraph_text = element.text.strip()
                paragraph = {"Text": paragraph_text,
                            "h1": title,
                            "h2": h2,
                            "h3": h3,
                            "h4": h4,
                            "h5": h5,
                            "h6": h6,}

paragraphs = parse_page_paragraphs(soup)