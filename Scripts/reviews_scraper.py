import steamreviews as SR
import pandas as pd
import heapq
import json

import spacy
from spacy.matcher import Matcher

from game_descriptors import game_subjs

# may need to improve json file loading, too much text may cause a problem
def load_or_download_reviews(app_id: str) -> dict:
    review_dict: dict = SR.load_review_dict(app_id)

    #print(review_dict)

    if review_dict['query_summary']['total_reviews'] == -1: # no file found
        SR.download_reviews_for_app_id(app_id)
        review_dict: dict = SR.load_review_dict(app_id)
    
    if review_dict['query_summary']['total_reviews'] == -1: # if query return -1 again, could not get reviews
        print(f"Error, could not find or download reviews for steam app %s" % app_id)
        return None

    return review_dict

def get_review_text_df(reviews: dict) -> pd.DataFrame:
    if reviews['query_summary']['total_reviews'] == -1:
        return {}

    review_text: list = [] 

    for review_id in reviews["reviews"]:
        review_text.append(reviews["reviews"][review_id]["review"]) # text of review

    df = pd.DataFrame(review_text, columns=["text"])

    return df

def process_summary_of_review_texts(data: pd.DataFrame):
    test_phrase: str = data.iloc[2]["text"]
    nlp = spacy.load('en_core_web_sm')

    doc = nlp(test_phrase)

    all_game_adjectives: dict = {
        "pairs": [],
        "adjectives": [],
    }

    for _, row in data.iterrows():
        review_text = row["text"]
        game_adjectives: dict = get_game_adjectives(nlp(review_text), nlp)

        all_game_adjectives["pairs"].extend(game_adjectives["pairs"])
        all_game_adjectives["adjectives"].extend(game_adjectives["adjectives"])

    #print(all_game_adjectives)
    #return

    #print(all_game_adjectives["pairs"])
    #print(all_game_adjectives["adjectives"])
    top_5_adjs: list = get_top_5_adjs(all_game_adjectives["adjectives"])
    top_5_pairs: list = get_top_5_pairs(all_game_adjectives["pairs"])

    summary = {
        "top_5_adjs": top_5_adjs,
        "top_5_pairs": top_5_pairs,
    }

    return summary

# filters out words that do not relate to a video game
def get_game_adjectives(doc, nlp) -> dict:
    output = {
        "pairs": [],
        "adjectives": [],
    }

    #print(doc)

    # get noun + adjective pairs
    pattern = [
    [{'POS':'ADJ'}, {'POS':'NOUN'}],
    ]

    matcher = Matcher(nlp.vocab)
    matcher.add("PAIRS", pattern)

    # currently does not filter out some special characters like "\[]""
    for _, start, end in matcher(doc):
        span = doc[start:end] # The matched span
        
        # only add pairs if the subject is a game-related noun
        # see game_descriptors for a list of subjects
        if (span.text.split()[1] in game_subjs):
            output["pairs"].append(span.lemma_)

    # Get adjectives with some filtering
    for token in doc:
        if token.pos_ == "ADJ" and not token.is_stop and token.is_alpha and len(token.text) != 1:
            #print(token.text)
            if(token.lemma_.isascii()):
                output["adjectives"].append(token.lemma_)
    
    #print(output["pairs"])
    #print(output["adjectives"])
    
    return output

def get_top_5_adjs(adj_list: list) -> list:
    occurences = dict()
    for adj in adj_list:
        if adj in occurences:
            occurences[adj] += 1
        else:
            occurences[adj] = 1

    heap = [(-count, adj) for adj, count in occurences.items()]
    heapq.heapify(heap)

    # If the number of unique adjectives is less than 5, adjust the range
    top_count = min(len(heap), 5)
    
    top_5 = [heapq.heappop(heap)[1] for _ in range(top_count)]

    return top_5

def get_top_5_pairs(pair_list: list) -> list:
    # subj : [totalOccurances, { adj: occurances... }]
    subj_occurences = dict() # this will have all of the words being filtered

    # O(n) convert list to dict
    for pair in pair_list:
        adj, subj = pair.split()

        if subj in subj_occurences:
            subj_occurences[subj][0] += 1
        else:
            subj_occurences[subj] = [1, {}]

        if adj in subj_occurences[subj][1]:
            subj_occurences[subj][1][adj] += 1
        else:
            subj_occurences[subj][1][adj] = 1

    # min_heap search O(n log k) + turning dict to min heap O(n)
    #print(subj_occurences)
    
    subj_heap = [(-count, subj) for subj, (count, _) in subj_occurences.items()]
    heapq.heapify(subj_heap)

    top_subj_count = min(len(subj_heap), 5) 
    top_5_subj = [heapq.heappop(subj_heap)[1] for _ in range(top_subj_count)]
    #print(top_5_subj)

    top_5_pairs: list = []

    # min_heap search for 5 subjects O(n log k) + turning adj list into min heap O(n)
    for top_subj in top_5_subj: 
        adj_heap = [(-count, adj) for adj, count in subj_occurences[top_subj][1].items()]
        #print(top_subj, adj_heap)
        heapq.heapify(adj_heap)

        top_5_pairs.append([top_subj, heapq.heappop(adj_heap)[1]])

    #print(subj_occurences)
    #print(top_5_pairs)

    return top_5_pairs

# store processed summary into .json file
def save_summary_to_json(app_id: str, summary) -> None:
    with open(f"data/summary_{app_id}.json", 'w+') as summary_file:
        json.dump(summary, summary_file)

def user_query_steam_id() -> None:
    user_input = input("Enter a valid steam ID: ")
    print("You entered : ", user_input)
    try:
        app_id = int(user_input)

        review_dict: dict = load_or_download_reviews(app_id)
        
        if review_dict == None: # if review could not be downloaded 
            user_query_steam_id()

        review_text_df: pd.DataFrame = get_review_text_df(review_dict)
        summary = process_summary_of_review_texts(review_text_df)
        print("Top 5 Adjectives: ", summary["top_5_adjs"], '\n', "Top 5 Pairs: " , summary["top_5_pairs"])
        save_summary_to_json(app_id, summary)

    except ValueError:
        print("ID must be a number, try again.")
        user_query_steam_id()

# testing
if __name__ == '__main__':
    user_query_steam_id()