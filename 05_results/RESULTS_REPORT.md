# 结果报告（L1 基线 + L2 对擂 + L3 稳健性 + L4 消融）

状态：L0 与全部确定性基线（250 run）、挑战者对擂（1230 run）、L3 稳健性与 L4 消融均已运行；L3/L4 结论见文末两节。

> 第 1 节为基线阶段的原始记录，保持原文不变；对擂与 L3/L4 记录追加在后。

- 协议 SHA-256：`c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`
- 协议冻结 SHA-256：`b97a9a31e36cea7d58ee9559c7dd90ac7f97fa9b0359594844e781cec5ba8b48`
- 复现命令：`python -X utf8 04_code/scripts/run_baselines.py`
- run 数：250
- 当前证据批次：末尾 50 个新 run；更早 200 个 run 按不可删除原则保留。
- 历史说明：首批 q4 暴露稀疏 JSON 未保存 IEEE-754 负零符号导致的因子字节哈希不一致，原 run 保持 CONSTRAINT_FAIL；修正后所有 baseline 均从头重跑。

| problem | N | K | q | status | RMSE | L | C | run-id |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| q1 | 2 | 1 | 16 | PASS | 4.32978028117747e-17 | 4 | 64 | `20260915T020512189095Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cc8e9ffed` |
| q1 | 4 | 2 | 16 | PASS | 1.48889641069474e-16 | 16 | 256 | `20260915T020512331325Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cc8e9ffed` |
| q1 | 8 | 3 | 16 | PASS | 3.14311158052417e-16 | 48 | 768 | `20260915T020512339512Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cc8e9ffed` |
| q1 | 16 | 4 | 16 | PASS | 6.90037553910599e-16 | 128 | 2048 | `20260915T020512352550Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cc8e9ffed` |
| q1 | 32 | 5 | 16 | PASS | 9.76280460130994e-16 | 320 | 5120 | `20260915T020512368122Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cc8e9ffed` |
| q1 | 64 | 6 | 16 | PASS | 1.31918012518583e-15 | 768 | 12288 | `20260915T020512392639Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cc8e9ffed` |
| q2 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T020512484981Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cc8e9ffed` |
| q2 | 4 | 1 | 3 | PASS | 0.5 | 0 | 0 | `20260915T020512495324Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cc8e9ffed` |
| q2 | 8 | 1 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T020512506792Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cc8e9ffed` |
| q2 | 16 | 1 | 3 | PASS | 0.25 | 0 | 0 | `20260915T020512517042Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cc8e9ffed` |
| q2 | 32 | 1 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T020512530026Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cc8e9ffed` |
| q3 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T020512546108Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cc8e9ffed` |
| q3 | 4 | 2 | 3 | PASS | 0.5 | 0 | 0 | `20260915T020512554198Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cc8e9ffed` |
| q3 | 8 | 3 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T020512565967Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cc8e9ffed` |
| q3 | 16 | 4 | 3 | PASS | 0.25 | 0 | 0 | `20260915T020512579890Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cc8e9ffed` |
| q3 | 32 | 5 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T020512606666Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cc8e9ffed` |
| q4 | 32 | 5 | 3 | CONSTRAINT_FAIL | 0.71839053240911 | 0 | 0 | `20260915T020512705661Z__q4__q4-b0-kron-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 2 | 1 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020512731766Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 2 | 2 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020512742084Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 2 | 3 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020512753567Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 4 | 1 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020512764594Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 4 | 2 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020512775696Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 4 | 3 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020512787967Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 4 | 4 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020512799824Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 8 | 1 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020512811839Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 8 | 2 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020512823967Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 8 | 3 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020512835890Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 8 | 4 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020512849949Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 8 | 5 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020512861943Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 16 | 1 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020512876292Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 16 | 2 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020512889765Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 16 | 3 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020512907519Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 16 | 4 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020512925793Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 16 | 5 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020512947265Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 16 | 6 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020512972011Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 32 | 1 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020512997934Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 32 | 2 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020513025900Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 32 | 3 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020513068848Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 32 | 4 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020513124735Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 32 | 5 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020513196344Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 32 | 6 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020513289714Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 32 | 7 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020513392421Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 1 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020513511275Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 2 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020513637009Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 3 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020513886611Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 4 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020514200409Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 5 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020514623747Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 6 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020515155387Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 7 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020515852314Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q5 | 64 | 8 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020516662529Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cc8e9ffed` |
| q1 | 2 | 1 | 16 | PASS | 4.32978028117747e-17 | 4 | 64 | `20260915T020658106747Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cf98eb4a9` |
| q1 | 4 | 2 | 16 | PASS | 1.48889641069474e-16 | 16 | 256 | `20260915T020658215403Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cf98eb4a9` |
| q1 | 8 | 3 | 16 | PASS | 3.14311158052417e-16 | 48 | 768 | `20260915T020658222807Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cf98eb4a9` |
| q1 | 16 | 4 | 16 | PASS | 6.90037553910599e-16 | 128 | 2048 | `20260915T020658230151Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cf98eb4a9` |
| q1 | 32 | 5 | 16 | PASS | 9.76280460130994e-16 | 320 | 5120 | `20260915T020658243338Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cf98eb4a9` |
| q1 | 64 | 6 | 16 | PASS | 1.31918012518583e-15 | 768 | 12288 | `20260915T020658267404Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cf98eb4a9` |
| q2 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T020658359585Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cf98eb4a9` |
| q2 | 4 | 1 | 3 | PASS | 0.5 | 0 | 0 | `20260915T020658367405Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cf98eb4a9` |
| q2 | 8 | 1 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T020658374107Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cf98eb4a9` |
| q2 | 16 | 1 | 3 | PASS | 0.25 | 0 | 0 | `20260915T020658381580Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cf98eb4a9` |
| q2 | 32 | 1 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T020658390210Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cf98eb4a9` |
| q3 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T020658403183Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cf98eb4a9` |
| q3 | 4 | 2 | 3 | PASS | 0.5 | 0 | 0 | `20260915T020658410572Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cf98eb4a9` |
| q3 | 8 | 3 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T020658417980Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cf98eb4a9` |
| q3 | 16 | 4 | 3 | PASS | 0.25 | 0 | 0 | `20260915T020658428622Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cf98eb4a9` |
| q3 | 32 | 5 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T020658450847Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cf98eb4a9` |
| q4 | 32 | 5 | 3 | PASS | 0.71839053240911 | 0 | 0 | `20260915T020658546205Z__q4__q4-b0-kron-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 2 | 1 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020658575261Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 2 | 2 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020658583365Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 2 | 3 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020658591821Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 4 | 1 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020658599457Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 4 | 2 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020658607258Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 4 | 3 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020658615786Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 4 | 4 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020658624280Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 8 | 1 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020658635965Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 8 | 2 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020658643483Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 8 | 3 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020658652381Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 8 | 4 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020658661866Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 8 | 5 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020658671502Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 16 | 1 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020658683564Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 16 | 2 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020658694485Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 16 | 3 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020658707775Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 16 | 4 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020658724560Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 16 | 5 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020658743470Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 16 | 6 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020658765007Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 32 | 1 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020658788777Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 32 | 2 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020658813247Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 32 | 3 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020658854172Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 32 | 4 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020658909599Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 32 | 5 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020658978982Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 32 | 6 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020659064152Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 32 | 7 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020659162493Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 1 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020659276776Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 2 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020659397220Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 3 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020659607539Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 4 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020659915785Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 5 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020700309563Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 6 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020700792799Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 7 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020701397925Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q5 | 64 | 8 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020702084360Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cf98eb4a9` |
| q1 | 2 | 1 | 16 | PASS | 4.32978028117747e-17 | 4 | 64 | `20260915T020833942378Z__q1__q1-b0-scaled-radix2__s0__pc253df79__ca54af176` |
| q1 | 4 | 2 | 16 | PASS | 1.48889641069474e-16 | 16 | 256 | `20260915T020834032195Z__q1__q1-b0-scaled-radix2__s0__pc253df79__ca54af176` |
| q1 | 8 | 3 | 16 | PASS | 3.14311158052417e-16 | 48 | 768 | `20260915T020834039440Z__q1__q1-b0-scaled-radix2__s0__pc253df79__ca54af176` |
| q1 | 16 | 4 | 16 | PASS | 6.90037553910599e-16 | 128 | 2048 | `20260915T020834047498Z__q1__q1-b0-scaled-radix2__s0__pc253df79__ca54af176` |
| q1 | 32 | 5 | 16 | PASS | 9.76280460130994e-16 | 320 | 5120 | `20260915T020834063035Z__q1__q1-b0-scaled-radix2__s0__pc253df79__ca54af176` |
| q1 | 64 | 6 | 16 | PASS | 1.31918012518583e-15 | 768 | 12288 | `20260915T020834089871Z__q1__q1-b0-scaled-radix2__s0__pc253df79__ca54af176` |
| q2 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T020834187412Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__ca54af176` |
| q2 | 4 | 1 | 3 | PASS | 0.5 | 0 | 0 | `20260915T020834195864Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__ca54af176` |
| q2 | 8 | 1 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T020834205993Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__ca54af176` |
| q2 | 16 | 1 | 3 | PASS | 0.25 | 0 | 0 | `20260915T020834213228Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__ca54af176` |
| q2 | 32 | 1 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T020834227041Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__ca54af176` |
| q3 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T020834241156Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__ca54af176` |
| q3 | 4 | 2 | 3 | PASS | 0.5 | 0 | 0 | `20260915T020834250339Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__ca54af176` |
| q3 | 8 | 3 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T020834259982Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__ca54af176` |
| q3 | 16 | 4 | 3 | PASS | 0.25 | 0 | 0 | `20260915T020834271070Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__ca54af176` |
| q3 | 32 | 5 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T020834294953Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__ca54af176` |
| q4 | 32 | 5 | 3 | PASS | 0.71839053240911 | 0 | 0 | `20260915T020834397417Z__q4__q4-b0-kron-butterfly__s0__pc253df79__ca54af176` |
| q5 | 2 | 1 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020834425408Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 2 | 2 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020834436497Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 2 | 3 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T020834443875Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 4 | 1 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020834450268Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 4 | 2 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020834457534Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 4 | 3 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020834464048Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 4 | 4 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T020834470497Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 8 | 1 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020834477885Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 8 | 2 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020834485398Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 8 | 3 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020834493174Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 8 | 4 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020834502644Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 8 | 5 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T020834512670Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 16 | 1 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020834525868Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 16 | 2 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020834537071Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 16 | 3 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020834549957Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 16 | 4 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020834565601Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 16 | 5 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020834585958Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 16 | 6 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T020834608301Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 32 | 1 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020834634197Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 32 | 2 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020834663185Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 32 | 3 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020834704259Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 32 | 4 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020834758798Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 32 | 5 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020834827363Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 32 | 6 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020834915233Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 32 | 7 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T020835013589Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 1 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020835128124Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 2 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020835238745Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 3 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020835451549Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 4 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020835757116Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 5 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020836160223Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 6 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020836651300Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 7 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020837295301Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q5 | 64 | 8 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T020838056631Z__q5__q5-b0-q1-butterfly__s0__pc253df79__ca54af176` |
| q1 | 2 | 1 | 16 | PASS | 4.32978028117747e-17 | 4 | 64 | `20260915T021051682870Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cd6fc5f40` |
| q1 | 4 | 2 | 16 | PASS | 1.48889641069474e-16 | 16 | 256 | `20260915T021051777868Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cd6fc5f40` |
| q1 | 8 | 3 | 16 | PASS | 3.14311158052417e-16 | 48 | 768 | `20260915T021051786996Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cd6fc5f40` |
| q1 | 16 | 4 | 16 | PASS | 6.90037553910599e-16 | 128 | 2048 | `20260915T021051798257Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cd6fc5f40` |
| q1 | 32 | 5 | 16 | PASS | 9.76280460130994e-16 | 320 | 5120 | `20260915T021051816120Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cd6fc5f40` |
| q1 | 64 | 6 | 16 | PASS | 1.31918012518583e-15 | 768 | 12288 | `20260915T021051848400Z__q1__q1-b0-scaled-radix2__s0__pc253df79__cd6fc5f40` |
| q2 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T021051947647Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cd6fc5f40` |
| q2 | 4 | 1 | 3 | PASS | 0.5 | 0 | 0 | `20260915T021051955828Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cd6fc5f40` |
| q2 | 8 | 1 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T021051970957Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cd6fc5f40` |
| q2 | 16 | 1 | 3 | PASS | 0.25 | 0 | 0 | `20260915T021051991461Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cd6fc5f40` |
| q2 | 32 | 1 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T021052002568Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__cd6fc5f40` |
| q3 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T021052024087Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cd6fc5f40` |
| q3 | 4 | 2 | 3 | PASS | 0.5 | 0 | 0 | `20260915T021052033844Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cd6fc5f40` |
| q3 | 8 | 3 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T021052043423Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cd6fc5f40` |
| q3 | 16 | 4 | 3 | PASS | 0.25 | 0 | 0 | `20260915T021052054510Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cd6fc5f40` |
| q3 | 32 | 5 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T021052080184Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__cd6fc5f40` |
| q4 | 32 | 5 | 3 | PASS | 0.71839053240911 | 0 | 0 | `20260915T021052184869Z__q4__q4-b0-kron-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 2 | 1 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T021052216107Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 2 | 2 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T021052229210Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 2 | 3 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T021052237789Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 4 | 1 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021052250139Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 4 | 2 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021052259773Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 4 | 3 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021052272747Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 4 | 4 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021052283080Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 8 | 1 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021052290961Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 8 | 2 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021052300312Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 8 | 3 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021052310571Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 8 | 4 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021052326636Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 8 | 5 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021052343463Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 16 | 1 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021052361695Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 16 | 2 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021052376894Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 16 | 3 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021052395482Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 16 | 4 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021052418652Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 16 | 5 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021052444017Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 16 | 6 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021052475414Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 32 | 1 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021052500734Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 32 | 2 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021052529392Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 32 | 3 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021052574728Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 32 | 4 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021052634470Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 32 | 5 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021052712508Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 32 | 6 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021052805075Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 32 | 7 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021052917706Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 1 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021053040892Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 2 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021053160270Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 3 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021053393919Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 4 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021053732610Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 5 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021054165553Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 6 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021054730577Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 7 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021055571625Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q5 | 64 | 8 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021056407085Z__q5__q5-b0-q1-butterfly__s0__pc253df79__cd6fc5f40` |
| q1 | 2 | 1 | 16 | PASS | 4.32978028117747e-17 | 4 | 64 | `20260915T021254422985Z__q1__q1-b0-scaled-radix2__s0__pc253df79__c8c947602` |
| q1 | 4 | 2 | 16 | PASS | 1.48889641069474e-16 | 16 | 256 | `20260915T021254571433Z__q1__q1-b0-scaled-radix2__s0__pc253df79__c8c947602` |
| q1 | 8 | 3 | 16 | PASS | 3.14311158052417e-16 | 48 | 768 | `20260915T021254580973Z__q1__q1-b0-scaled-radix2__s0__pc253df79__c8c947602` |
| q1 | 16 | 4 | 16 | PASS | 6.90037553910599e-16 | 128 | 2048 | `20260915T021254596435Z__q1__q1-b0-scaled-radix2__s0__pc253df79__c8c947602` |
| q1 | 32 | 5 | 16 | PASS | 9.76280460130994e-16 | 320 | 5120 | `20260915T021254616724Z__q1__q1-b0-scaled-radix2__s0__pc253df79__c8c947602` |
| q1 | 64 | 6 | 16 | PASS | 1.31918012518583e-15 | 768 | 12288 | `20260915T021254650456Z__q1__q1-b0-scaled-radix2__s0__pc253df79__c8c947602` |
| q2 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T021254768421Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__c8c947602` |
| q2 | 4 | 1 | 3 | PASS | 0.5 | 0 | 0 | `20260915T021254786098Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__c8c947602` |
| q2 | 8 | 1 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T021254800571Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__c8c947602` |
| q2 | 16 | 1 | 3 | PASS | 0.25 | 0 | 0 | `20260915T021254816315Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__c8c947602` |
| q2 | 32 | 1 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T021254831935Z__q2__q2-b0-onefactor-quantize__s0__pc253df79__c8c947602` |
| q3 | 2 | 1 | 3 | PASS | 0.292893218813453 | 0 | 0 | `20260915T021254853249Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__c8c947602` |
| q3 | 4 | 2 | 3 | PASS | 0.5 | 0 | 0 | `20260915T021254864104Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__c8c947602` |
| q3 | 8 | 3 | 3 | PASS | 0.353553390593274 | 0 | 0 | `20260915T021254877272Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__c8c947602` |
| q3 | 16 | 4 | 3 | PASS | 0.25 | 0 | 0 | `20260915T021254896970Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__c8c947602` |
| q3 | 32 | 5 | 3 | PASS | 0.176776695296637 | 0 | 0 | `20260915T021254928124Z__q3__q3-b0-quantized-butterfly__s0__pc253df79__c8c947602` |
| q4 | 32 | 5 | 3 | PASS | 0.71839053240911 | 0 | 0 | `20260915T021255035742Z__q4__q4-b0-kron-butterfly__s0__pc253df79__c8c947602` |
| q5 | 2 | 1 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T021255069857Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 2 | 2 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T021255084131Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 2 | 3 | 1 | INFEASIBLE | 0.292893218813453 | 0 | 0 | `20260915T021255098390Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 4 | 1 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021255112626Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 4 | 2 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021255130228Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 4 | 3 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021255146753Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 4 | 4 | 1 | INFEASIBLE | 0.5 | 0 | 0 | `20260915T021255162629Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 8 | 1 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021255177229Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 8 | 2 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021255192929Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 8 | 3 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021255210616Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 8 | 4 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021255227208Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 8 | 5 | 1 | INFEASIBLE | 0.353553390593274 | 0 | 0 | `20260915T021255247782Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 16 | 1 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021255266846Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 16 | 2 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021255284679Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 16 | 3 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021255305828Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 16 | 4 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021255330117Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 16 | 5 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021255359127Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 16 | 6 | 1 | INFEASIBLE | 0.25 | 0 | 0 | `20260915T021255389786Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 32 | 1 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021255423050Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 32 | 2 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021255458294Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 32 | 3 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021255511970Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 32 | 4 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021255579162Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 32 | 5 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021255661530Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 32 | 6 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021255759037Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 32 | 7 | 1 | INFEASIBLE | 0.176776695296637 | 0 | 0 | `20260915T021255875555Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 1 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021256003176Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 2 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021256128126Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 3 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021256353751Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 4 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021256676629Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 5 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021257086590Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 6 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021257591078Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 7 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021258199333Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |
| q5 | 64 | 8 | 1 | INFEASIBLE | 0.125 | 0 | 0 | `20260915T021258909558Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602` |

所有数值均来自本轮新 run，并在各自 `run_manifest.json` 中绑定目标、因子、代码树、协议及冻结哈希。独立复算从持久化稀疏因子文件重新加载并计算。

问题 5 中 `INFEASIBLE` 表示因子合法但 `RMSE>0.1`；它不是运行失败，也不得被当作胜者。


---

## L2 对擂结果（追加）
- 汇总 run 数：1480（被拒 0，0 表示全部 manifest 可解析且路径存在）
- 状态分布：`{"CONSTRAINT_FAIL": 1, "INFEASIBLE": 957, "PASS": 522}`
- 协议 SHA-256：`c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`

| 问题 | 注册候选 | 运行数 | 可行运行数 | winner | winner 依据 | winner RMSE | L | C |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| q1 | 3 | 66 | 66 | `q1-b0-scaled-radix2` | feasible | 4.329780281e-17 | 4 | 64 |
| q2 | 3 | 235 | 235 | `q2-b0-onefactor-quantize` | feasible | 0.1767766953 | 0 | 0 |
| q3 | 3 | 175 | 175 | `q3-b0-quantized-butterfly` | feasible | 0.1767766953 | 0 | 0 |
| q4 | 3 | 47 | 46 | `q4-c1-generic-discrete` | feasible | 0.1841023057 | 0 | 0 |
| q5 | 3 | 957 | 0 | `q5-b0-q1-butterfly` | best_structurally_valid_but_rmse_above_threshold | 0.125 | 0 | 0 |

### 问题 5 的实质结论

问题 5 的全部运行均不可行（`RMSE > 0.1`），最好值为 `0.125`，并非搜索强度不足：约束 2 要求系数实虚部为整数，故任意合法乘积逐元素属于高斯整数环 `Z[i]`；单位化目标每项模长 `1/sqrt(N)`，任取 `z in Z[i]` 有 `|f - z| >= min(1/sqrt(N), 1 - 1/sqrt(N))`，于是 `RMSE >= d_N`，而 `d_64 = 1/8 = 0.125 > 0.1`，冻结六实例的可行域为空。证明见 `03_model/Q5_GAUSSIAN_INTEGER_INFEASIBILITY.md`，本分支已独立复算 `d_N`。

因此 `05_results/tournament.json` 中问题 5 的 `winner_id` 标注为 `winner_basis = "best_structurally_valid_but_rmse_above_threshold"`：它是约束合法但超出阈值的最好运行，**不是可行解**。终局文本应写「已证明不可行」，不得写成「在预算内未找到」。

## L3 稳健性（追加，`05_results/l3_robustness.json`）

协议要求每个挑战者在每个注册实例上跑满种子 `{17, 43, 71}` 并保留失败运行，这些运行即种子稳健性证据，故 L3 在**已记录的运行集上测量**，不重复执行。

| 问题 | 状态 | 种子覆盖完整 | 测量实例数 | 结合顺序检查 |
| --- | --- | --- | ---: | --- |
| q1 | PASS | True | 12 | PASS |
| q2 | PASS | True | 70 | PASS |
| q3 | PASS | True | 50 | PASS |
| q4 | PASS | True | 14 | PASS |
| q5 | PASS | True | 264 | PASS |

- 每个 (问题, 实例, 候选) 组内报告跨种子最好 / 中位 / 最差 RMSE 与极差；
- 独立复算容差沿用协议值 `1e-10`；
- 乘法结合顺序：对记录因子按左结合与右结合重建乘积，最大逐元素差不超 `1e-9`。

边界：L3 未新增种子运行，只测量协议已要求的三种子覆盖。

## L4 消融（追加，`05_results/l4_ablation.json`）

协议点名的四种消融已在本脚本内实跑（非引用）：`no_hierarchical_init`、`no_support_reconnect`、`no_discrete_polish`、`fixed_butterfly_vs_reconnectable`。

| 问题 | 状态 | 测量数 |
| --- | --- | ---: |
| q1 | PASS | 8 |
| q2 | PASS | 8 |
| q3 | PASS | 8 |
| q4 | PASS | 8 |
| q5 | PASS | 32 |

每条记录含 `rmse_full`、`rmse_ablated` 与 `delta`。边界：消融以「关闭组件后重跑」实现，粒度较粗；测量数受 `--ablation-instances` 限制，未覆盖全部注册实例。

## 结论与限制（追加）

1. 问题 1 的 winner 为精确构造（`RMSE <= 1.4e-15`，`N=2..64`），且 `L` 与该问题确定性基线一致；
2. 问题 2/3/4 的 winner 在各自 `(N,K,q)` 上是本次运行集内的最好可行运行，按协议写作 `best_found`；本次挑战者未在 q3 上超过基线，不主张改进；
3. 问题 5 已证明不可行，`winner_id` 仅为约束合法的最好运行，不是可行解；
4. L3/L4 状态来自实测文件，不是声明；两者均未覆盖全部注册实例（见各自边界）；
5. `metrics.json` 与 `tournament.json` 由 `aggregate_results.py` 从已提交的 run manifest 确定性重建，可重复执行。
