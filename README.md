# SteamReviewCruncher
Crunches down steam reviews to the 5 top adjectives and subject-adjective pairs that describe a game.

Upon running reviews_scraper.py, enter in a valid steam game app_id in the terminal.
The program retrieves steam reviews at a limited rate of 10 reviews per second. See the steamreviews page (https://pypi.org/project/steamreviews/) for more information.
These reviews will then have game-related adjectives filtered out, as well as adjective-noun pair patterns. The adjectives in the former and subjects in the latter are
compared to sets of game-related words in game_descriptors.py to further filter out non-relevant game words.

The program will return the top 5 most common adjectives and adjective-noun pairs using min-heap search.

Dependencies:
  pandas
  steamreviewws
  spacy
