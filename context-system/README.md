# Context-System

这个文件夹内是 yarns 系统中的 context 管理系统。
该部分其实有点像一个个人的知识管理系统，但是更加专注于上下文理解和管理。

context-system 的目标是：
> 让用户的 yarns agent 可以充分理解用户，然后预测用户潜在需求，直接调用 subagents ，利用相关的用户 context 更好地解决用户潜在需求。一切以用户体验为中心。
> More context, more understanding, more accurate. 所以 yarno agent 也需要尽可能多的优质 context 来更好的理解用户。

## 系统是如何组织的？
一切以 markdown 文档为中心。

- ai-space
    - about-me
        - shallow
        - deep
    - records
- my-space
- tempo-space
    - chat-history
    - notes

从下往上看，
1. 首先是 tempo-space，其中 chat-history 存放用户与 yarno agent 的聊天记录，原封不动的存储即可。notes 存放用户的临时思考和记录，例如灵感，备忘等。
2. 然后是 my-space，my-space 是用户的持久工作区，用户可以在这里撰写**需要反复查看和修改的内容**，沉淀有价值的 context 产出，也可以保存一些网络上的优质资料等等。用户可以自行创建自文件夹定义分类规则，例如以 projects，thinkings，materials 为子分类。
3. 最上层是是 ai-space，其中一个重要的模块是 about-me，分为两部分，一部分是 shallow，另一部分是 deep。shallow 即表象，是故事、经历、事实、直接思考等，来自于 ai 总结 my-space 和 tempo-space 的内容，并对内容进行总结摘要等。而 deep 则是 ai 对 shallow 的表象进行深刻的行为学，心理学进行分析所得到的内容，表现为用户的深层偏好，行为习惯特征等等。该部分主要由 ai 进行自动管理，用户可以查看编辑。

