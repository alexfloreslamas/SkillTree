# Path: src
import yaml
import pprint
from networkx import Graph
from pyvis.network import Network
import re


class SkillTree:
    def __init__(self, skills_file: str):
        self.configs:           dict[str | int, dict | list] = self._read_file(skills_file)
        self.max_proficiency:   int = self.configs["network_config"]["max_proficiency"]
        self.edge_width:        int = self.configs["network_config"]["edge_width"]
        self.edge_color:        str = self.configs["network_config"]["edge_color"]
        self.tree:              Graph = Graph()
        # ---
        if self.configs["network_config"]["legends"]:
            self._add_legends()
        self._tree_builder()
        nt:                     Network = self._network_config()
        self._draw_and_save_network(nt)

    # ------------------- #
    # >>> Reads yaml file #
    # ------------------- #

    @staticmethod
    def _read_file(skills_file: str) -> dict[str | int, dict | list]:
        with open(skills_file) as f:  # Loads the config file
            configs = yaml.load(f, Loader=yaml.FullLoader)
        return configs

    # ---------------------- #
    # >>> The __str__ method #
    # ---------------------- #

    def __str__(self) -> str:
        # Shows the config file:
        text:                   str = pprint.pformat(self.configs, compact=False) + "\n\n"

        # Shows the graph's info
        if self.configs["network_config"]["legends"]:
            text += f"Graph with {self.tree.order()-self.max_proficiency} nodes and "
            text += f"{self.tree.size(weight=None)- (self.max_proficiency - 1)} edges\n"

            if self.max_proficiency == 1:
                return text + "There is 1 additional node with a legend"
            return text + f"There are {self.max_proficiency} legend nodes and {self.max_proficiency - 1} edges"
        return text + f"{self.tree}"

    # ----------------------- #
    # >>> Builds legend graph #
    # ----------------------- #

    def _add_legends(self) -> None:
        # legend nodes
        step:                   int = 50
        x:                      int = -600
        y:                      int = 0
        legend_nodes:           list[tuple[str, dict]] = [
            (
                str(idx),
                {
                    'label': f"Skill level: {idx+1}/{self.max_proficiency}",
                    'fixed': False,  # So that we can move the legend nodes around to arrange them better
                    'physics': True,
                    'x': x,
                    'y': y - idx * step,
                    'shape': 'box',
                    'color': leaf_color,
                }
            )
            for idx, leaf_color in enumerate(self.configs['network_config']['leaf_colors'])
        ]
        self.tree.add_nodes_from(legend_nodes)

        for i in range(0, len(legend_nodes) - 1):
            self.tree.add_edge(
                legend_nodes[i][0], legend_nodes[i+1][0], weight=self.edge_width, color=self.edge_color, smooth=False
            )

    # ----------------------- #
    # >>> Builds skills graph #
    # ----------------------- #

    def _tree_builder(self) -> None:
        level:                  int = 0
        for key, item in self.configs.items():
            if key != "network_config":
                self.tree.add_node(
                    key,
                    size=self.configs["network_config"]["nodes_sizes"][level],
                    color=self.configs["network_config"]["internal_colors"][level],
                )
                self._tree_builder_aux(key, self.configs[key], level + 1)

    def _tree_builder_aux(self, parent_id: str, a_dict: dict[str | int, dict | list], level: int) -> None:
        for key, item in a_dict.items():
            if isinstance(item, dict):  # i.e., "key" = child is a str, "item" is a dict; adding internal nodes
                self.tree.add_node(
                    key,
                    size=self.configs["network_config"]["nodes_sizes"][level],
                    color=self.configs["network_config"]["internal_colors"][level],
                )
                self.tree.add_edge(parent_id, key, weight=self.edge_width, color=self.edge_color, smooth=False)
                self._tree_builder_aux(key, a_dict[key], level + 1)

            else:
                # "key" = skill ability from 1 to "max_proficiency". The higher, the better; for this reason, we need to
                # scale the node size accordingly see variable "scaled_size".
                # "item" is a list containing the children or in this case the leaves.
                # Adding leaves
                scaled_size:    int = (self.configs["network_config"]["nodes_sizes"][-1] / self.max_proficiency) * key
                leaves:         list[str] = a_dict[key]
                for leaf in leaves:
                    self.tree.add_node(
                        leaf,
                        size=scaled_size,
                        title=f"Skill level: {key}/{self.max_proficiency}",
                        color=self.configs["network_config"]['leaf_colors'][key-1]
                    )
                    self.tree.add_edge(parent_id, leaf, weight=self.edge_width, color=self.edge_color, smooth=False)

    # ------------------------- #
    # >>> Sets network settings #
    # ------------------------- #

    def _network_config(self) -> Network:
        nt = Network(
            height="750px",
            width="100%",
            bgcolor=self.configs["network_config"]["bgcolor"],
            font_color=self.configs["network_config"]["font_color"],
            heading=self.configs["network_config"]["title"],
            # select_menu=True
        )
        nt.repulsion(node_distance=100, central_gravity=0.2, spring_length=65, spring_strength=0.05, damping=0.09)

        return nt

    # -------------------------------------------- #
    # >>> plots everything and saves the html file #
    # -------------------------------------------- #

    def _draw_and_save_network(self, nt: Network) -> None:
        nt.from_nx(self.tree)
        # nt.show_buttons(filter_=['nodes'])
        # nt.show_buttons(filter_=['edges'])
        # nt.show_buttons(filter_=['physics'])
        nt.save_graph('./Output/skill_tree.html')

        # To remove the double heading in the HTML file, we execute the following code, taken and adapted from:
        # - https://stackoverflow.com/questions/74890203/pyvis-network-has-double-heading

        # Edits the heading and removes the first occurrence:
        html_str = re.sub(r'<center>.+?</h1>\s+</center>', '', nt.html, 1, re.DOTALL)

        h = open('./Output/skill_tree.html', 'w')
        h.write(html_str)
        h.close()
        # The double-heading issue has already been reported:
        # - https://github.com/WestHealth/pyvis/issues/219
