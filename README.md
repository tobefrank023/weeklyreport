# Weekly Reports

## 研究记录

### 2026-10-28：金融材料篡改检测小试

使用 Codex CLI + `gpt-6-luna`（medium effort）执行 30 道题：18 道单文档判断、12 道原改对比，来自 21 组原件。实际为整页看图直答，没有工具探索。

临时内容完成分为 **52.5/100**，未纳入定位框评分；这是一轮开发可行性小试，不是正式 benchmark 成绩。

- [实验说明：题目格式、解题方式、评分与局限](reports/2026-10-28-financial-material-pilot/EXPERIMENT_NOTE.md)
- [4 道真实案例：题面、局部示例、标注答案与模型回答](reports/2026-10-28-financial-material-pilot/CASE_EXAMPLES.md)
- [机器可读的汇总结果](reports/2026-10-28-financial-material-pilot/data/summary.json)

公开内容不包含内部整页材料、完整题库或访问凭据。案例中的局部图是阅读示例，模型实际输入为整页图片。

### 2026-10-28：CAD 调研与实验进展汇总

完成 CAD Benchmark、Agent 与模型调研，并在物理机上开展 CADTestBench 全量、失败题恢复及 BenchCAD 九个公开样例的三模型实验。汇总包含原始/v2 评分、成本、案例、协议边界和后续研究建议，明确区分单次成绩与多阶段累计覆盖。

- [阶段汇总：全部实验结果、成本与研究判断](reports/2026-10-28-CAD.md)
- [完整 CAD 调研：2026-10-22 历史快照](references/CAD-survey-2026-10-22.md)
- [原 CAD 项目目标说明](references/CAD-agent.md)
- [原始实验与完整轨迹](https://github.com/cai-yutao/CAD-agent/tree/6c45380541c2480bf6695f8aa87bf705fa893a72)
