# mdutils

该模块提供了对文本文档（不仅限于 `markdown` 文档）的批量处理和字数统计功能，以及相应的命令行工具。

This module provides batch processing and word count functions for text files (not only `.md`) and corresponding command line tools.

## mdutils.iterdir

该函数递归获取所有指定后缀的文件的路径，并返回一个元素为 `pathlib.Path` 实例的列表对象。

This function recursively gets paths of all files with suffixes that is specified, and returns a list object of which the elements are instances of `pathlib.Path`.

## mdutils.format

该函数可通过传入自定义的格式化函数改变其行为。

This function can modify its behavior by passing custom formatting function.

**注意**，默认的格式化函数仅应用于 `markdown` 文档，详见 `mdutils.__formatfunc_default` 的具体实现。

**Note** that the default formatting function should only be applied to `markdown` files. Read the implementation of `mdutils.__formatfunc_default` for details.

## mdutils.stats

该函数提供字数统计。

This function provide word count.

## command line tools

请使用 `-h` 选项获取更多帮助。

Please use option `-h` for further help.

## 写在后面的话

写文档好累啊，又没人看。具体使用细节完全没有提及，总之详情请见源码。
