---
name: wewrite-visual
description: |
  WeWrite 视觉模块：为公众号文章生成封面和必要的内文配图，或只交付提示词。触发词：
  封面图、公众号配图、给文章配图、换封面。通用绘图和 logo 设计不触发。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
---

# wewrite-visual — 封面与配图

## 前置

用户指定文章时使用该文件；否则 `wewrite run show`，读取当前任务的 `artifacts.article`、
`artifacts.illustrated_article`、`artifacts.image_prompts`、`artifacts.images_manifest`、
`visual`、`flags` 和任务目录。已完成的文章也可以直接配图，不要恢复或新建写作任务。

读取 `{home}/style.yaml` 的 `cover_style`、`cover_reference` 和 `cover_template`。
本轮要求优先于账号偏好，账号偏好优先于通用视觉指南。`cover_reference` 是视觉参考图，
使用前实际打开，仅参考信息层级和主体表达，不直接复用；只有明确设置 `cover_template`
才使用固定封面。未设置固定模板时，每次按当前文章重新设计封面，不因历史封面已有而跳过。

有任务时运行 `wewrite run step visual in_progress`。用户直接给了任务外文章时独立执行，
不写任务状态；提示词和图片放进文章同目录的 `<文件名>-assets/`，带图副本写成
`<文件名>-illustrated.md`。

根据本轮原话确定模式并用 `wewrite run update` 记录：只要封面用 `cover`，封面和必要内文图
用 `full`，只要提示词用 `prompts`。不要沿用写作模式猜测用户想生图。`prompts` 或
`skip_image_gen=true` 时仍要完成提示词，但不调用付费图片服务。

完整读取：

```text
读取: {skill_dir}/references/visual-guide.md
```

## 执行

用户只要资讯原有配图时，直接收集、检查并插入已有素材，不触发下面的生图步骤。
遵循账号 `editorial_layout.illustrations` 和 `gallery`：保留相关且不重复的原图、演示动图，
注明出处；同一事件多图使用 `:::gallery`。检查最终 HTML 的横向图轨，不能只检查 Markdown
容器或“左右滑动”提示存在；动图角标等块级内容不得插到图轨中导致换行。原始素材不强制裁成
16:9，也不强行统一摄影、图表与截图的风格。完成后保存素材清单、来源和带图副本。

1. 从终稿提取 3-5 个具体实体和文章主情绪，形成统一色板、构图与质感；用户已有风格
   要求时优先沿用。将核心实体与正文中的具体事件对应，并写进提示词，按视觉指南检查内容辨识度。
2. 写一个封面提示词。`cover` 模式只规划封面，继续后续生成与检查；`full` 模式只为确实
   需要解释或缓冲阅读的段落补图，不按固定数量凑图。
3. 将提示词和目标路径写到 `artifacts.image_prompts`；批量清单写到
   `artifacts.images_manifest`。
4. 数量必须不超过任务的 `visual.max_images`。调用时同时传入数量和费用上限：

```bash
wewrite image-gen --manifest {run_dir}/images.json --max-images {max_images} --max-cost {max_cost}
```

`max_cost` 为空时省略该参数。预算预检不通过就减少内文图，不能绕过上限。图片服务失败时
保留完整提示词并继续流程。

5. 按视觉指南一次性检查所有实际文件：能打开、格式与扩展名一致、核心实体可辨、
   风格连贯。只重试
   明显失败的单张一次。`full` 模式先复制原始正文到 `artifacts.illustrated_article`，再把
   采用的内文图插到副本相应段落；封面不插入正文。任何模式都不得覆盖原始正文。

完成后更新 `images.cover`、`images.figures`，再执行：

```bash
wewrite run step visual completed
```

只有提示词时同样标 completed，并明确说明未产生费用、没有实际图片。
