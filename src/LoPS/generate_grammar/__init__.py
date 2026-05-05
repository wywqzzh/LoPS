"""generate_grammar 包的公共入口。

该 package 只暴露常用配置对象；数据读取、状态图、scoring、grammar 学习和
结构化输出逻辑分别放在同级模块中，避免入口文件承载业务细节。
"""

from .config import GenerateGrammarConfig, GrammarLearningParams

__all__ = ["GenerateGrammarConfig", "GrammarLearningParams"]
