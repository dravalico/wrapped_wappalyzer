![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
![Google Chrome](https://img.shields.io/badge/Google%20Chrome-4285F4?style=for-the-badge&logo=GoogleChrome&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/-selenium-%43B02A?style=for-the-badge&logo=selenium&logoColor=white)

# WrappedWappalyzer

As the name suggests, this repository contains a wrapper for the [Wappalyzer](https://github.com/HTTPArchive/wappalyzer)
Chrome extension, in its open source version, updated to April 1, 2024. The goal of this (small) project is to provide
an automated tool (using [Selenium](https://www.selenium.dev/) for Python) for visiting websites and extracting the
analysis done through Wappalyzer, which in its original version offers no API.

## Prerequisites and usage

can be run in two different methods, i.e., by running `main.py` with Python or by using Docker.
Either way, a single target (URL or domain) can be visited, and the technologies detected by Wappalyzer will be printed
to `stdout` formatted as JSON. Additionally, it saves DNS information (A, AAAA, CNAME, NS and TXT) and if A record has
NXDOMAIN status, the visit through Selenium is aborted. It also checks if the website is reachable using `curl`; it
check the exit code and the http code and if there is an error or the http code is different from 2xx or 3xx, it saves
data and quit.

The entrypoint receives three parameters:

1. `--target` the target to contact, it is mandatory. If only one domain is specified, `https://` will be added in front
2. `--timeout` it is optional and, it is used to specify the maximum time to wait for the page to load, then the driver
   will be closed
3. `--attempts` the maximum number of attempts to perform to contact the target (optional)

### Via Docker

This is the easiest way, since you only need Docker installed to pull the prebuilt image
from [this DockerHub repo](https://hub.docker.com/repository/docker/dravalico/wrapped-wappalyzer/general). This image
uses [browsertime](https://hub.docker.com/r/sitespeedio/browsertime/) since it provide Chrome 135 with all its
dependencies. Please note that it also downloads the ChromeDriver, as the default one is not updated.

```sh
docker pull dravalico/wrapped-wappalyzer:1.0
docker run dravalico/wrapped-wappalyzer:1.0 --target example.com
```

The [`parallel_visits.sh`](parallel_visits.sh) script provides and easy way to contact many targets using the GNU shell
tool [`parallel`](https://www.gnu.org/software/parallel/). You need to specify the list of URLs or domains to be
contacted (in the example `targets`), the file in which to save the results, which will be a JSONL (`out`), and the
number of cores to be used (here, 3).

```sh
git clone https://github.com/dravalico/wrapped_wappalyzer
cd wrapped_wappalyzer
chmod +x parallel_visits.sh
./parallel_visits.sh targets out 3
```

If you want to build and run your image by editing [this Dockerfile](Dockerfile), after the changes run the following

```sh
docker build -t wrapped-wappalyzer .
docker run wrapped-wappalyzer --target example.com
```

> [!CAUTION]
> When using Chrome in multiple processes, it is important to limit the hardware resources for each one. In this script,
> each container is limited to using at most 1 cpu (`--cpus=1`) and 3 gigabytes of main memory (`--memory=3g`). Also,
> via the `--rm` parameter, when the process terminates, the container is deleted to avoid using too much host space.

### Via Python

If you want to run the tool using Python you will need to have installed:

- Python (and pip or similar to install Selenium)
- [Chrome](https://www.google.it/intl/en/chrome/?brand=JJTC&ds_kid=43700059034491703&gclsrc=aw.ds&gad_source=1)
- [ChromeDriver](https://developer.chrome.com/docs/chromedriver/downloads)

and then

```sh
git clone https://github.com/dravalico/wrapped_wappalyzer
cd wrapped_wappalyzer
pip install requirements.txt
```

Next, after installing Chrome and downloading ChromeDriver, the latter must be moved to `/usr/local/bin` on Unix
systems (*for Windows I have no idea, but after all, who uses Winzoz?*) and then give it execution permissions.

```sh
mv chromedriver-linux64/chromedriver /usr/local/bin/ 
chmod +x /usr/local/bin/chromedriver
```

Finally, since with this method there is no script to perform parallel visits, to visit a URL or domain just run

```sh
python main.py --target example.com
```

Note that the Chrome browser will be opened in headless mode, meaning that you won't see the page open and close.
