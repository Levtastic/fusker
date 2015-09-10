import urllib.request, urllib.error
import itertools

class termcol:
    enabled = True
    colours = {
        "red":      "\033[91m",
        "pink":     "\033[95m",
        "green":    "\033[92m",
        "yellow":   "\033[93m",
    }
    endchar = "\033[0m"

    @classmethod
    def wrap(cls, s, colour):
        if not cls.enabled or colour not in cls.colours:
            return s

        return cls.colours[colour] + s + cls.endchar

try:
    import colorama
    colorama.init()
except ImportError:
    import os, platform
    if platform.system() == "Windows" and os.environ.get("TERM", "") != "ANSI":
        termcol.enabled = False

class urlstats:
    downloaded = 0
    not_found = 1
    failed = 2

class Fusker:
    echo = lambda self, s: print(s, end = "", flush = True)
    downloaded = notfound = failed = 0

    def get(self, pattern):
        urls = self.build_urls("", self.split(pattern))

        len_urls = len(urls)
        print(str.format("This will attempt {} URLs.", len_urls))
        print("Example: " + termcol.wrap(max(urls, key = len), "pink"))
        if not self.ask_yes_no("Proceed?"):
            print("Fetch aborted.")
            return

        try:
            for url in urls:
                self.url_retrieve(url)
        except KeyboardInterrupt:
            print("\nCancelled.")

        self.output_stats()

    def split(self, pattern):
        left, right = "[", "]"

        pieces = []
        piece = ""
        dynamic = False

        for char in pattern:
            if char == (dynamic and right or left):
                if piece:
                    pieces.append((piece, dynamic))
                    piece = ""

                dynamic = not dynamic

            else:
                piece += char

        if piece:
            pieces.append((piece, dynamic))

        return pieces

    def build_urls(self, built_url, remaining_pieces):
        if not remaining_pieces:
            return [built_url]

        else:
            text, dynamic = remaining_pieces[0]
            remaining_pieces = remaining_pieces[1:]

            if dynamic:
                urls = []
                for bit in self.expand(text):
                    urls += self.build_urls(built_url + bit, remaining_pieces)

                return urls

            else:
                return self.build_urls(built_url + text, remaining_pieces)

    def expand(self, dynamic):
        statics = []
        for piece in str.split(dynamic, ","):
            if "-" in piece:
                try:
                    first, second = str.split(piece, "-", 1)
                    statics += self.get_range(first, second)

                except ValueError:
                    statics.append(piece)

            else:
                statics.append(piece)

        return statics

    def get_range(self, first, second):
        if str.isdigit(first) and str.isdigit(second):
            digits = len(first)
            return [str.zfill(str(n), digits) for n in range(int(first), int(second) + 1)]

        lists = []
        for i in range(min(len(first), len(second))):
            lists.append([chr(c) for c in range(ord(first[i]), ord(second[i]) + 1)])

        return [str.join('', tup) for tup in itertools.product(*lists)]

    def ask_yes_no(self, querytext):
        while True:
            print(querytext + " (Y/N)")
            choice = str.lower(input())

            if choice:
                if choice[0] == "y":
                    return True

                elif choice[0] == "n":
                    return False

            print("Unrecognised input. Please enter one of Y/N/Yes/No.")

    def url_retrieve(self, url):
        filename = str.rsplit(url, "/", 1)[-1]

        try:
            urllib.request.urlretrieve(url, filename)
            self.log_url_attempt(urlstats.downloaded)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.log_url_attempt(urlstats.not_found)

            else:
                self.log_url_attempt(urlstats.failed)

        except ValueError:
            self.log_url_attempt(urlstats.failed)

    def log_url_attempt(self, status):
        if status == urlstats.downloaded:
            self.echo(termcol.wrap(".", "green"))
            self.downloaded += 1
            return

        if status == urlstats.not_found:
            self.echo(termcol.wrap("_", "yellow"))
            self.notfound += 1
            return

        if status == urlstats.failed:
            self.echo(termcol.wrap("x", "red"))
            self.failed += 1
            return

    def output_stats(self):
        total = str(self.downloaded + self.notfound + self.failed)
        print("\n")
        print("URLs Attempted: " + total)
        print("-" * (len(total) + 16))
        print(termcol.wrap("Downloaded (.): " + str(self.downloaded), "green"))
        print(termcol.wrap("Not Found  (_): " + str(self.notfound), "yellow"))
        print(termcol.wrap("Failed     (x): " + str(self.failed), "red"))

        self.downloaded = self.notfound = self.failed = 0

if __name__ == "__main__":
    import sys
    pattern = str.join(' ', [arg for arg in sys.argv if arg != __file__])

    if str.replace(str.replace(str.replace(pattern, "-", ""), "/", ""), "\\", "") in ("", "?", "help"):
        print("Example usage:")
        print(termcol.wrap("fusk http://example.com/images/img_[0-10]_[A-G][,_final].[jpg,png,bmp]", "pink"))
        print("The tool will then attempt to download all the URLs that match the pattern.")
        print("For example: " + termcol.wrap("http://example.com/images/img_9_D_final.bmp", "pink"))

    else:
        Fusker().get(pattern)
