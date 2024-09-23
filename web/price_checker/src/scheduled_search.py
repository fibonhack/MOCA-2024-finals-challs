import json
from utils.ebayApi import ebay_research
from pathlib import Path
import json
import sys

def search(user):
    folder = Path(
        "/results",
        f"{user}_last_search"
    )
    if folder.is_dir():
        for file_path in folder.glob('*'):
            if file_path.is_file():
                with file_path.open('r') as file:
                    data = json.load(file)
                # TODO: generalize once we add mode stores
                result = ebay_research("http://api.ebay.com", data['title'])
                if result['price']['value'] <= data['price']['value']:
                    with open(file_path, 'w') as file:
                        file.write(json.dumps(result))
                    #TODO: send mail to notify the user that the price is changed!

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    user = sys.argv[1]
    search(user)
