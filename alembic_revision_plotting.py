import os
import sys
import json
import datetime

first_arg = sys.argv[1]


class AlembicRevisionNetworkCreator(object):

    def __init__(self, versions_path):
        self.versions_path = versions_path

    def _get_version_and_down_revisions(self, filename):

        with open(os.path.join(self.versions_path, filename)) as f:
            file_text = f.read()

        # Lines clean-up and lower-cased.
        matched_lines = [' '.join(line.lower().split()) for line in file_text.split('\n') if "revision = " in line]
        revision = None
        down_revisions = []

        for line in matched_lines:
            line = line.replace("'", "").replace('"', '').replace(")", "").replace("(", "")
            if 'down' in line:
                down_revisions = line.split("down_revision = ", 1)[1].replace(' ', '').split(',')
            else:
                revision = line.split("revision = ", 1)[1]

        return revision, down_revisions

    def get_links(self):

        links = []
        for filename in os.listdir(self.versions_path):
            if filename.endswith(".asm") or filename.endswith(".py"):

                revision, down_revisions = self._get_version_and_down_revisions(filename)
                for down_revision in down_revisions:
                    if down_revision:
                        links.append({
                            'source': down_revision,
                            'target': revision
                        })

        return links


if __name__ == "__main__":
    if not first_arg:
        print("Please provide a path to analyze!")
        quit()

    graph_data_creator = AlembicRevisionNetworkCreator(first_arg)
    links = json.dumps(graph_data_creator.get_links())

    with open('force-graph-template.html') as f:
        force_graph_html_template = f.read()
        force_graph_html_template = force_graph_html_template.replace("'<insert_links_here>'", links)

    new_filename = 'force-graph-template-{}.html'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    with open(new_filename, "w") as f:
        f.write(force_graph_html_template)
