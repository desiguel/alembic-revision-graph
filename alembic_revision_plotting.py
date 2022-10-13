import os
import sys
import json
import datetime
import getopt
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class AlembicRevisionMetaData:
    revision: str
    down_revisions: List[str]
    author: str


@dataclass
class NetworkLink:
    from_revision: AlembicRevisionMetaData
    to_revision: AlembicRevisionMetaData


class AlembicRevisionNetworkCreator(object):

    def __init__(self, versions_path: str):
        self.versions_path = versions_path

    def _get_alembic_metadata_from_revision_file(self, filename: str) -> AlembicRevisionMetaData:

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

        # Get file author. Assume that this is the person who made the most commits.
        author = "todo"

        return AlembicRevisionMetaData(revision, down_revisions, author)

    def get_links(self) -> List[NetworkLink]:

        links = []
        for filename in os.listdir(self.versions_path):
            if filename.endswith(".asm") or filename.endswith(".py"):

                alembic_revision_metadata = self._get_alembic_metadata_from_revision_file(filename)
                for down_revision in alembic_revision_metadata.down_revisions:
                    if down_revision:
                        links.append(NetworkLink(down_revision, revision))
        return links

    @staticmethod
    def get_end_nodes(links: List[NetworkLink]) -> List[str]:

        target_usage_count = defaultdict(int)
        target_usage_count['none'] += 1  # Increase 'none' node count so it doesn't show.

        for network_link in links:
            target_usage_count[network_link.to_revision] += 1
            target_usage_count[network_link.from_revision] += 1

        # End nodes will only have one entry in the list of network links. Take advantage of this to identify them.
        return [target for target, count in target_usage_count.items() if count == 1]

    @staticmethod
    def get_target_sources_dict(links):

        target_sources = defaultdict(list)
        for source_target_dict in links:
            target_sources[source_target_dict['target']].append(source_target_dict['source'])
        return target_sources

    @staticmethod
    def get_target_sources(target_sources_dict, end_node):
        sources = []
        for target, inner_sources in target_sources_dict.items():
            if target == end_node:
                sources += inner_sources
        return sources

    def get_pruned_tree_sources(self, links, max_tree_depth):

        end_nodes = self.get_end_nodes(links)
        target_sources_dict = self.get_target_sources_dict(links)
        source_list = self.get_pruned_source_list(end_nodes, target_sources_dict, max_tree_depth)
        return set(source_list)

    def get_pruned_source_list(self, targets, target_sources_dict, depth_running_total):

        target_sources = []
        if depth_running_total > 0:
            target_sources += targets
            for target in targets:
                sources_sources = self.get_target_sources(target_sources_dict, target)
                if sources_sources:
                    target_sources += self.get_pruned_source_list(
                        sources_sources,
                        target_sources_dict,
                        depth_running_total - 1
                    )
        return target_sources

    def pruned_get_links(self, max_tree_depth):
        links = self.get_links()
        pruned_tree_sources = self.get_pruned_tree_sources(links, max_tree_depth)
        return [link for link in links if link['source'] in pruned_tree_sources]


def main(argv):
    versions_directory = ''
    max_tree_depth = None
    try:
        opts, args = getopt.getopt(argv, "hv:d:", ["help=", "versions_directory=", "max_tree_depth="])
    except getopt.GetoptError:
        print('alembic_revision_plotting.py -v <versions_directory> [-d <max_tree_depth>]')
        sys.exit(2)

    if len(opts) == 0:
        print('alembic_revision_plotting.py -v <versions_directory> [-d <max_tree_depth>]')
        sys.exit(2)

    for opt, arg in opts:

        if opt in ("-h", "--help"):
            print('alembic_revision_plotting.py -v <versions_directory> [-d <max_tree_depth>]')
            sys.exit()
        elif opt in ("-v", "--versions_directory"):
            versions_directory = arg
        elif opt in ("-d", "--max_tree_depth"):
            try:
                max_tree_depth = float(arg)
            except ValueError:
                print("Max tree depth provide is not a number!")

    graph_data_creator = AlembicRevisionNetworkCreator(versions_directory)
    link_list_dict = json.dumps(
        graph_data_creator.pruned_get_links(max_tree_depth) if max_tree_depth else graph_data_creator.get_links()
    )

    with open('force-graph-template.html') as f:
        force_graph_html_template = f.read()
        force_graph_html_template = force_graph_html_template.replace("'<insert_links_here>'", link_list_dict)

    new_filename = 'force-graph-template-{}.html'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    with open(new_filename, "w") as f:
        f.write(force_graph_html_template)


if __name__ == "__main__":
    main(sys.argv[1:])
