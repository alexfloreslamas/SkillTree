# Path:
from src.skill_tree import SkillTree

if __name__ == "__main__":
    print(f"\nRunning {__file__}\n")

    skills_file = './Input/Skills.yml'
    st = SkillTree(skills_file)
    print(st)
