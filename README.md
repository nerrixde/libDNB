# LibDNB

<img alt="LibDNB" src="https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue">  <img alt="PyPI - Status badge" src="https://img.shields.io/badge/status-stable-brightgreen">  <img alt="PRs welcome" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg">

> This project is *heavily* inspired by [calibre-dnb](https://github.com/citronalco/calibre-dnb)


## About
I needed a way to fetch basic book metadata from the German National Libraries "API", I found [calibre-dnb](https://github.com/citronalco/calibre-dnb), but it is not suitable for my usage case, so I modified it.
You can visit the portal here: [portal.dnb.de](https://portal.dnb.de).

## Get started

### Obtain Token
You need to apply for an API-Key at schnittstellen-service@dnb.de in order to get access to the catalogue. This library uses the `SRU-API`, you need a `SRU Access Token`.

### Installation
`pip install libdnb`

### Usage
Code Example:
```py
import libdnb

dnbclient = libdnb.LibDNB("Your-SRU-Access-Token-Here")
result = dnbclient.lookup("9783346111098") # ISDN, Title, or any other metadata to search for here
if result: # Result might be None if nothing was found
    print(result["title"])
```
#### Fields
| Key | Datatype |
| -- | -- |
| `title` | String |
| `authors` | String |
| `author_sort` | List |
| `languages` | List |
| `pubdate` | datetime.datetime |
| `publisher_location` | String |
| `publisher_name` | String |
| `subtitle` | String |
| `tags` | List |
| `comments` | String |
| `isbn` | String |
| `urn` | String |
| `idn` | String |
| `ddc` | String |

> Note that some fields might be empty, you have to figure out on which fields you want to rely upon.
