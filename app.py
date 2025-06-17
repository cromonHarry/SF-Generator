# ============================
# 改良版近未来SF生成器 - 日文多轮对话版
# ============================
import streamlit as st
import json
import re
import time
from openai import OpenAI
import wikipedia
import requests

# ========== Multi-page setup ==========
if 'page' not in st.session_state:
    st.session_state.page = "main"

# ========== Visualization Page ==========
if st.session_state.page == "visualization":
    st.set_page_config(page_title="APモデル可視化", layout="wide")
    
    st.title("🔬 APモデル可視化")
    st.markdown("APモデルの3段階の進化を可視化します。")
    
    # Check if AP model data exists
    if 'ap_history' in st.session_state and st.session_state.ap_history:
        # Create the HTML visualization
        html_content = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APモデル可視化</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 95vw;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .vis-wrapper {
            overflow-x: auto;
            border: 1px solid #ddd;
            border-radius: 10px;
        }
        
        .visualization {
            position: relative;
            width: 2200px;
            height: 700px;
            background: #fafafa;
        }
        
        .node {
            position: absolute;
            width: 140px;
            height: 140px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: bold;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border: 3px solid white;
            line-height: 1.2;
            padding: 15px;
            box-sizing: border-box;
        }
        
        .node:hover {
            transform: scale(1.1);
            z-index: 100;
        }
        
        /* Node Colors */
        .node-前衛的社会問題 { background: #ff9999; }
        .node-人々の価値観 { background: #ecba13; }
        .node-社会問題 { background: #ffff99; }
        .node-技術や資源 { background: #99cc99; }
        .node-日常の空間とユーザー体験 { background: #99cccc; }
        .node-制度 { background: #9999ff; }
        
        .arrow {
            position: absolute;
            height: 2px;
            background: #333;
            transform-origin: left center;
            z-index: 1;
        }
        
        .arrow::after {
            content: '';
            position: absolute;
            right: -8px;
            top: -4px;
            width: 0;
            height: 0;
            border-left: 8px solid #333;
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
        }
        
        .arrow-label {
            position: absolute;
            background: white;
            padding: 2px 8px;
            border: 1px solid #ddd;
            border-radius: 15px;
            font-size: 10px;
            white-space: nowrap;
            transform: translate(-50%, -50%);
            z-index: 10;
        }
        
        .dotted-arrow {
            border-top: 2px dotted #333;
            background: transparent;
        }
        
        .dotted-arrow::after {
            border-left-color: #333;
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
            max-width: 300px;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            line-height: 1.4;
        }
        
        .tooltip.show {
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center; margin-bottom: 30px;">APモデル可視化</h1>
        
        <div class="vis-wrapper">
            <div class="visualization" id="visualization">
            </div>
        </div>
        
        <div class="tooltip" id="tooltip"></div>
    </div>

    <script>
        const visualization = document.getElementById('visualization');
        const tooltip = document.getElementById('tooltip');
        let allNodes = {};

        // Load AP model data from session state
        const apModelData = ''' + json.dumps(st.session_state.ap_history, ensure_ascii=False) + ''';

        function getNodePosition(stageIndex, nodeType) {
            const stageWidth = 700;
            const xOffset = stageIndex * stageWidth;
            
            if (stageIndex % 2 === 0) { 
                switch(nodeType) {
                    case '制度':                      return { x: xOffset + 355, y: 50 };
                    case '日常の空間とユーザー体験':  return { x: xOffset + 180, y: 270 };
                    case '社会問題':                  return { x: xOffset + 530, y: 270 };
                    case '技術や資源':              return { x: xOffset + 50,  y: 500 };
                    case '前衛的社会問題':            return { x: xOffset + 355, y: 500 };
                    case '人々の価値観':              return { x: xOffset + 660, y: 500 };
                    default:                        return null;
                }
            } else { 
                switch(nodeType) {
                    case '技術や資源':              return { x: xOffset + 50,  y: 50 };
                    case '前衛的社会問題':            return { x: xOffset + 355, y: 50 };
                    case '人々の価値観':              return { x: xOffset + 660, y: 50 };
                    case '日常の空間とユーザー体験':  return { x: xOffset + 180, y: 270 };
                    case '社会問題':                  return { x: xOffset + 530, y: 270 };
                    case '制度':                      return { x: xOffset + 355, y: 500 };
                    default:                        return null;
                }
            }
        }

        function renderAllStages() {
            visualization.innerHTML = '';
            allNodes = {}; 

            apModelData.forEach((stageData, stageIndex) => {
                stageData.ap_model.nodes.forEach(nodeData => {
                    const position = getNodePosition(stageIndex, nodeData.type);
                    if (!position) return;

                    const node = document.createElement('div');
                    node.className = `node node-${nodeData.type}`;
                    node.style.left = position.x + 'px';
                    node.style.top = position.y + 'px';
                    node.textContent = nodeData.type;
                    node.dataset.definition = nodeData.definition;
                    node.dataset.id = `s${stageData.stage}-${nodeData.type}`;

                    node.addEventListener('mouseenter', showTooltip);
                    node.addEventListener('mouseleave', hideTooltip);

                    visualization.appendChild(node);
                    allNodes[node.dataset.id] = node;
                });
            });

            apModelData.forEach((stageData, stageIndex) => {
                const nextStage = apModelData[stageIndex + 1];

                stageData.ap_model.arrows.forEach(arrowData => {
                    const isLastStage = !nextStage;
                    const arrowType = arrowData.type;
                    const typesToHideInLastStage = ['標準化', '組織化', '意味付け', '習慣化'];

                    if (isLastStage && typesToHideInLastStage.includes(arrowType)) {
                        return;
                    }
                    
                    let sourceNode = allNodes[`s${stageData.stage}-${arrowData.source}`];
                    let targetNode;
                    let isInterStage = false;

                    if (nextStage && (arrowType === '組織化' || arrowType === '標準化')) {
                        targetNode = allNodes[`s${nextStage.stage}-技術や資源`];
                        isInterStage = !!targetNode;
                    } else if (nextStage && arrowType === '意味付け') {
                        targetNode = allNodes[`s${nextStage.stage}-日常の空間とユーザー体験`];
                        isInterStage = !!targetNode;
                    } else if (nextStage && arrowType === '習慣化') {
                        targetNode = allNodes[`s${nextStage.stage}-制度`];
                        isInterStage = !!targetNode;
                    }

                    if (!isInterStage) {
                        targetNode = allNodes[`s${stageData.stage}-${arrowData.target}`];
                    }

                    if (sourceNode && targetNode) {
                        const isDotted = arrowData.type === 'アート（社会批評）' || arrowData.type === 'アート(社会批評)' || arrowData.type === 'メディア';
                        createArrow(sourceNode, targetNode, arrowData, isDotted);
                    }
                });
            });
        }

        function createArrow(sourceNode, targetNode, arrowData, isDotted) {
            const nodeRadius = 70;
            
            const startPos = { x: parseFloat(sourceNode.style.left), y: parseFloat(sourceNode.style.top) };
            const endPos = { x: parseFloat(targetNode.style.left), y: parseFloat(targetNode.style.top) };

            const dx = (endPos.x + nodeRadius) - (startPos.x + nodeRadius);
            const dy = (endPos.y + nodeRadius) - (startPos.y + nodeRadius);
            const distance = Math.sqrt(dx * dx + dy * dy);
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;

            const adjustedStartX = startPos.x + nodeRadius + (dx / distance) * nodeRadius;
            const adjustedStartY = startPos.y + nodeRadius + (dy / distance) * nodeRadius;
            const adjustedDistance = distance - (nodeRadius * 2);

            const arrow = document.createElement('div');
            arrow.className = isDotted ? 'arrow dotted-arrow' : 'arrow';
            arrow.style.left = adjustedStartX + 'px';
            arrow.style.top = adjustedStartY + 'px';
            arrow.style.width = adjustedDistance + 'px';
            arrow.style.transform = `rotate(${angle}deg)`;

            const label = document.createElement('div');
            label.className = 'arrow-label';
            label.textContent = arrowData.type;
            
            const labelX = adjustedStartX + (dx / distance) * (adjustedDistance / 2);
            const labelY = adjustedStartY + (dy / distance) * (adjustedDistance / 2);
            label.style.left = labelX + 'px';
            label.style.top = labelY + 'px';
            
            label.dataset.definition = arrowData.definition;
            label.addEventListener('mouseenter', showTooltip);
            label.addEventListener('mouseleave', hideTooltip);

            visualization.appendChild(arrow);
            visualization.appendChild(label);
        }

        function showTooltip(event) {
            const definition = event.target.dataset.definition;
            if (definition) {
                tooltip.innerHTML = definition;
                tooltip.style.left = (event.pageX + 15) + 'px';
                tooltip.style.top = (event.pageY - 10) + 'px';
                tooltip.classList.add('show');
            }
        }

        function hideTooltip() {
            tooltip.classList.remove('show');
        }

        // Initialize visualization
        renderAllStages();
    </script>
</body>
</html>
        '''
        
        # Display the HTML content
        st.components.v1.html(html_content, height=800, scrolling=True)
        
        # Download options
        st.subheader("ダウンロードオプション")
        col1, col2 = st.columns(2)
        
        with col1:
            ap_json = json.dumps(st.session_state.ap_history, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 APモデルJSONをダウンロード",
                data=ap_json,
                file_name="ap_model.json",
                mime="application/json"
            )
        
        with col2:
            if 'story' in st.session_state and st.session_state.story:
                st.download_button(
                    label="📥 SF小説をダウンロード",
                    data=st.session_state.story,
                    file_name="sf_story.txt",
                    mime="text/plain"
                )
    
    else:
        st.warning("可視化するAPモデルデータがありません。メインページでAPモデルを生成してください。")
    
    if st.button("⬅ メインページに戻る"):
        st.session_state.page = "main"
        st.rerun()
    st.stop()

# ========== Main Page ==========
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# System prompt in Japanese
SYSTEM_PROMPT = """君はサイエンスフィクションの専門家であり、「アーキオロジカル・プロトタイピング（Archaeological Prototyping, 以下AP）」モデルに基づいて社会を分析します。以下はこのモデルの紹介です。
APは、18の項⽬(6個の対象と12個射)によって構成される社会⽂化モデル(Sociocultural model)である。要するに、ある課題をテーマとして、社会や⽂化を18この要素に分割し、そのつながりを論理的に描写したモデルである。
このモデルは、有向グラフとしても考えることができます。6つの対象（前衛的社会問題、⼈々の価値観、社会問題、技術や資源、⽇常の空間とユーザー体験、制度）と12の射（メディア、コミュニティ化、⽂化芸術振興、標準化、コミュニケーション、組織化、意味付け、製品・サービス、習慣化、パラダイム、ビジネスエコシステム、アート（社会批評））で⼀世代の社会⽂化モデルを構成する。これらの対象と射のつながりは、以下の定義で示されます。

##対象
1. 前衛的社会問題: 技術や資源のパラダイムによって引き起こされる社会問題や⽇常⽣活が営まれる空間やそこでのユーザーの体験に対してアート(社会批評)を介して顕在化される社会問題。
2. ⼈々の価値観: ⽂化芸術振興を通して広められる前衛的社会問題や⽇常のコミュニケーションによって広められる制度で対応できない社会問題に共感する⼈々のありたい姿。この問題は誰もが認識しているのではなく、ある⼀部の先進的な/マイノリティの⼈々のみが認識する。具体的には、マクロの環境問題(気候・⽣態など)と⼈⽂環境問題(倫理・経済・衛⽣など)が含まれる。
3. 社会問題: 前衛的問題に取り組む先進的なコミュニティによって社会に認識される社会問題やメディアを介して暴露される制度で拘束された社会問題。社会において解決すべき対象として顕在化される。
4. 技術や資源: ⽇常⽣活のルーティンを円滑に機能させるために作られた制度のうち、標準化されて過去から制約を受ける技術や資源であり、社会問題を解決すべく組織化された組織(営利・⾮営利法⼈、法⼈格を持たない集団も含み、新規・既存を問わない)が持つ技術や資源。
5. ⽇常の空間とユーザー体験: 技術や資源を動員して開発された製品・サービスによって構成される物理的空間であり、その空間で製品・サービスに対してある価値観のもとでの意味づけを⾏い、それらを使⽤するユーザーの体験。価値観とユーザー体験の関係性は、例えば、 「AI エンジニアになりたい」という価値観を持った⼈々が、PC に対して「プログラミングを学習するためのもの」という意味づけを⾏い、 「プログラミング」という体験を⾏う、というようなものである。
6. 制度: ある価値観を持った⼈々が⽇常的に⾏う習慣をより円滑に⾏うために作られる制度や、⽇常の空間とユーザー体験を構成するビジネスを⾏う関係者(ビジネスエコシステム)がビジネスをより円滑に⾏うために作られる制度。具体的には、法律やガイドライン、業界標準、⾏政指導、モラルが挙げられる。

##射
1. メディア : 現代の制度的⽋陥を顕在化させるメディア。マスメディアやネットメディア等の主要なメディアに加え、情報発信を⾏う個⼈も含まれる。制度を社会問題に変換させる。(制度 -> 社会問題)
2. コミュニティ化: 前衛的な問題を認識する⼈々が集まってできるコミュニティ。公式か⾮公式かは問わない。前衛的社会問題を社会問題に変換させる。 (前衛的社会問題 -> 社会問題)
3. ⽂化芸術振興: アート(社会批評)が顕在化させた社会問題を作品として展⽰し、⼈々に伝える活動。前衛的社会問題を⼈々の価値観に変換させる。 (前衛的社会問題 -> ⼈々の価値観)
4. 標準化 : 制度の中でも、より広い関係者に影響を与えるために⾏われる制度の標準化。制度を新しい技術·資源に変換させる。 (制度 -> 技術·資源)
5. コミュニケーション: 社会問題をより多くの⼈々に伝えるためのコミュニケーション⼿段。例えば、近年は SNS を介して⾏われることが多い。社会問題を⼈々の価値観に変換させる。 (社会問題 -> ⼈々の価値観)
6. 組織化 : 社会問題を解決するために形成される組織。法⼈格の有無や新旧の組織かは問わず 、新しく⽣まれた社会問題に取り組む全ての組織。社会問題を新しい技術·資源に変換させる。 (社会問題 -> 技術·資源)
7. 意味付け : ⼈々が価値観に基づいて製品やサービスを使⽤する理由。⼈々の価値観を新しい⽇常の空間とユーザー体験に変換させる。 (⼈々の価値観 -> ⽇常の空間とユーザー体験)
8. 製品・サービス: 組織が保有する技術や資源を利⽤して創造する製品やサービス。技術·資源を⽇常の空間とユーザー体験に変換させる。 (技術·資源 -> ⽇常の空間とユーザー体験)
9. 習慣化 : ⼈々が価値観に基づいて⾏う習慣。⼈々の価値観を制度に変換させる。 (⼈々の価値観 -> 制度)
10. パラダイム : その時代の⽀配的な技術や資源として、次世代にも影響をもたらすもの。技術·資源を前衛的社会問題に変換させる。 (技術·資源 -> 前衛的社会問題)
11. ビジネスエコシステム: ⽇常の空間やユーザー体験を維持するために、構成する製品・サービスに関わる関係者が形成するネットワーク 。⽇常の空間とユーザー体験を制度に変換させる。 (⽇常の空間とユーザー体験 -> 制度)
12. アート(社会批評): ⼈々が気づかない問題を、主観的/内発的な視点で⾒る⼈の信念。⽇常の空間とユーザー体験に違和感を持ち、問題を提⽰する役割を持つ。⽇常の空間とユーザー体験を前衛的社会問題に変換させる。 (⽇常の空間とユーザー体験 -> 前衛的社会問題)

###Sカーブは、時間の経過に伴うテクノロジーの進化を表すモデルです。以下の3つの段階で構成され、各段階の説明は次のとおりです。
##第1段階：揺籃期: この段階では、技術開発は着実に進歩しますが、その進展は緩やかです。主として既存の問題解決や現行機能の改善に焦点が当てられます。この期間の終わりには、現在の問題が解決される一方で、新たな問題が発生します。
##第2段階：離陸期: この段階では、テクノロジーは急成長期に入ります。様々な革新的なアイデアが提案され、それらが最終的に組み合わさることで、全く新しい形の技術が生まれます。この期間の終わりには、テクノロジーは大きな発展を遂げますが、同時に新たな問題も引き起こします。
##第3段階：成熟期: この段階では、技術の発展は再び緩やかになります。前期で発生した問題を解決しつつ、テクノロジーはより安定的で成熟した状態へと進化していきます。
"""

# Initialize session state
if 'conversation_step' not in st.session_state:
    st.session_state.conversation_step = 0
if 'user_inputs' not in st.session_state:
    st.session_state.user_inputs = {}
if 'wikipedia_candidates' not in st.session_state:
    st.session_state.wikipedia_candidates = []
if 'selected_topic' not in st.session_state:
    st.session_state.selected_topic = None
if 'selected_content' not in st.session_state:
    st.session_state.selected_content = None
if 'ap_history' not in st.session_state:
    st.session_state.ap_history = []
if 'descriptions' not in st.session_state:
    st.session_state.descriptions = []
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'generating' not in st.session_state:
    st.session_state.generating = False

# Helper functions
def parse_json_response(gpt_output: str) -> dict:
    result_str = gpt_output.strip()
    if result_str.startswith("```") and result_str.endswith("```"):
        result_str = re.sub(r'^```[^\n]*\n', '', result_str)
        result_str = re.sub(r'\n```$', '', result_str)
        result_str = result_str.strip()
    
    try:
        return json.loads(result_str)
    except Exception as e:
        raise e

def search_wikipedia_candidates(keyword: str, max_results: int = 5):
    """Wikipedia検索結果から候補を取得"""
    wikipedia.set_lang("ja")
    
    try:
        results = wikipedia.search(keyword, results=max_results)
        candidates = []
        
        for result in results:
            try:
                page = wikipedia.page(result, auto_suggest=False)
                summary = wikipedia.summary(result, sentences=1)
                candidates.append({
                    "title": result,
                    "summary": summary,
                    "content": page.content
                })
            except Exception as e:
                continue
        
        return candidates
    except Exception as e:
        return []

def create_introduction_from_content(product: str, content: str) -> str:
    """Wikipedia内容から製品紹介を生成"""
    user_prompt = f"""
これは{product}に関するwiki記事です、その内容をまとめて、{product}の紹介を出力してください。100字日本語以内。
###記事内容:
{content}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0
    )
    return response.choices[0].message.content

def analyze_content_with_gpt(product: str, content: str) -> dict:
    """第1段階用：Wikipedia内容からAP要素を抽出"""
    user_prompt = f"""
これから、{product}を紹介する記事を提示します。あなたのタスクは、その内容からAPモデルで定義されている各対象および射に関連する記述や文を抽出することです。
出力は、nodes(対象)とarrows(射)の2つのリストを持つJSON形式としてください。

- 各AP対象については、以下の形式でnodesに追加してください：
{{"type": "<<対象名>>", "definition": "<記事内容から導き出される簡潔かつ文脈に即した説明>", "reference": "<その対象を示す記事の引用文>"}}

- 各AP射については、以下の形式でarrowsに追加してください：
{{"source": "<起点対象>", "target": "<終点対象>", "type": "<射名>", "definition": "<記事内容から導き出される簡潔かつ文脈に即した説明>", "reference": "<その射を示す記事の引用文>"}}

なお、[起点対象, 終点対象, 射]の組み合わせは、APモデルで定義された関係性に従っている必要があります。該当する内容が見つからない場合は、リストを空のまま返してください。
###記事内容:
{content}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )
    
    return parse_json_response(response.choices[0].message.content)

def update_to_next_stage(product: str, ap_model: list[dict], description: list[str], imagination: str, stage: int):
    """次段階への更新内容を生成"""
    temp = f"""
今は{product}に関するAPモデルを次のSカーブ段階に更新してください。以下はAPモデルの情報です：
"""
    for i in range(len(ap_model)):
        temp += f"##第{i+1}段階のAPモデル:\n{ap_model[i]}\n"
    for j in range(len(description)):
        temp += f"##第{j+1}段階の{product}の説明:\n{description[j]}\n"
    if stage == 2:
        temp += f"##これは第{stage}段階の{product}に関する想像です：\n{imagination}\n"
        
    temp += f"""
Sカーブに基づき、第{stage}段階における新しい対象「技術や資源」と「⽇常の空間とユーザー体験」を分析し、対象内容を出力してください。
そして、第{stage}段階における{product}の構想を分析し、{product}の紹介を出力してください。100字日本語以内。

以下のJSON形式で出力してください：
{{"introduction": "第{stage}段階の{product}の100字以内の紹介", 
"tech_resources": "第{stage}段階技術や資源の具体的内容", 
"daily_experience": "第{stage}段階日常の空間とユーザー体験の具体的内容"}}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": temp}
        ],
        temperature=0
    )
    
    try:
        result = parse_json_response(response.choices[0].message.content)
        return result["introduction"], result["tech_resources"], result["daily_experience"]
    except Exception as e:
        return f"第{stage}段階の{product}の発展", "技術や資源の内容", "日常の空間とユーザー体験の内容"

def update_ap_model(product: str, ap_model: list[dict], description: list[str], tech_resources: str, daily_experience: str, stage: int) -> dict:
    """第2、3段階の完全なAPモデルを構築（必ず6対象+12射）"""
    user_prompt = f"""
これから第{stage}Sカーブ段階のAPモデルを構築してください。

##前段階の情報:
第{stage-1}段階の{product}の説明: {description[stage-2]}
第{stage-1}段階のAPモデル: {ap_model[stage-2]}

##現段階の情報:
構想：{description[stage-1]}
技術や資源：{tech_resources}
日常の空間とユーザー体験：{daily_experience}

**重要**：第{stage}段階では、必ず以下の6個の対象と12個の射すべてを含めてください：

対象: 前衛的社会問題、⼈々の価値観、社会問題、技術や資源、⽇常の空間とユーザー体験、制度
射: メディア、コミュニティ化、⽂化芸術振興、標準化、コミュニケーション、組織化、意味付け、製品・サービス、習慣化、パラダイム、ビジネスエコシステム、アート(社会批評)

以下のJSON形式で出力してください：
{{"nodes": [{{"type": "対象名", "definition": "この対象に関する説明"}}], "arrows": [{{"source": "起点対象", "target": "終点対象", "type": "射名", "definition": "この射に関する説明"}}]}}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )
    
    try:
        result = parse_json_response(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"nodes": [], "arrows": []}

def generate_story(product: str, ap_model: list[dict], description: list[str]) -> str:
    """SF短編小説を生成"""
    user_prompt = f"""
以下は{product}に関するAPモデルの情報です：
"""
    for i in range(len(ap_model)):
        user_prompt += f"""
##第{i+1}段階のAPモデル:
{ap_model[i]}
##第{i+1}段階の{product}の説明:
{description[i]}

"""
    user_prompt += f"""
それでは{product}をテーマとしてAPモデルの内容を基づき、近未来短編SF小説を生成してください。**重要**: 文字数は日本語1000字程度で。
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
    )

    return response.choices[0].message.content

# Main UI
st.title("🚀 近未来SF生成器")
st.markdown("APモデルに基づいて3段階の進化タイムラインとSF小説を生成するアプリケーションです。")

# Multi-step conversation interface
if st.session_state.conversation_step == 0:
    st.subheader("ステップ1: 興味のある事柄")
    st.markdown("あなたの興味のある事柄についてAPモデルを構築し、SF短編小説を生成します。")
    
    interest = st.text_input("どのようなことに興味がありますか？", 
                            placeholder="例：食べ物、技術、文化など",
                            key="interest_input")
    
    if st.button("次へ進む", disabled=not interest):
        st.session_state.user_inputs['interest'] = interest
        # Search Wikipedia
        with st.spinner("Wikipediaで検索中..."):
            candidates = search_wikipedia_candidates(interest)
            st.session_state.wikipedia_candidates = candidates
        st.session_state.conversation_step = 1
        st.rerun()

elif st.session_state.conversation_step == 1:
    st.subheader("ステップ2: テーマの選択")
    st.markdown(f"「{st.session_state.user_inputs['interest']}」に関する検索結果から選択してください。")
    
    if st.session_state.wikipedia_candidates:
        for i, candidate in enumerate(st.session_state.wikipedia_candidates):
            with st.expander(f"{candidate['title']}", expanded=False):
                st.markdown(f"**概要**: {candidate['summary']}")
                if st.button(f"「{candidate['title']}」を選択", key=f"select_{i}"):
                    st.session_state.selected_topic = candidate['title']
                    st.session_state.selected_content = candidate['content']
                    st.session_state.conversation_step = 2
                    st.rerun()
    else:
        st.warning("検索結果が見つかりませんでした。他のキーワードで試してください。")
        if st.button("戻る"):
            st.session_state.conversation_step = 0
            st.rerun()

elif st.session_state.conversation_step == 2:
    st.subheader("ステップ3: 未来の発展方向")
    st.markdown(f"「{st.session_state.selected_topic}」が未来にどのような方向に発展してほしいですか？")
    
    direction = st.radio(
        "発展方向を選択してください:",
        ["技術革新", "体験向上", "環境保護"],
        key="direction_radio"
    )
    
    if st.button("次へ進む"):
        st.session_state.user_inputs['direction'] = direction
        st.session_state.conversation_step = 3
        st.rerun()

elif st.session_state.conversation_step == 3:
    st.subheader("ステップ4: 未来のビジョン")
    st.markdown("一文で、この対象が未来にどのような姿になってほしいか描写してください。")
    
    vision = st.text_area("未来のビジョン", 
                         placeholder="例：より持続可能で効率的な技術として社会に貢献する姿",
                         key="vision_input")
    
    if st.button("次へ進む", disabled=not vision):
        st.session_state.user_inputs['vision'] = vision
        st.session_state.conversation_step = 4
        st.rerun()

elif st.session_state.conversation_step == 4:
    st.subheader("ステップ5: 個人的なシナリオ")
    st.markdown("あなた自身がその未来の姿と関わるシナリオを想像して描写してください。")
    
    scenario = st.text_area("個人的なシナリオ", 
                           placeholder="例：私はその技術を使って新しいサービスを開発し、多くの人の生活を改善したい",
                           key="scenario_input")
    
    if st.button("次へ進む", disabled=not scenario):
        st.session_state.user_inputs['scenario'] = scenario
        st.session_state.conversation_step = 5
        st.rerun()

elif st.session_state.conversation_step == 5:
    st.subheader("入力内容の確認")
    st.markdown("以下の内容でAPモデルを構築します。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**選択したテーマ:**")
        st.info(st.session_state.selected_topic)
        st.markdown("**発展方向:**")
        st.info(st.session_state.user_inputs['direction'])
        
    with col2:
        st.markdown("**未来のビジョン:**")
        st.info(st.session_state.user_inputs['vision'])
        st.markdown("**個人的なシナリオ:**")
        st.info(st.session_state.user_inputs['scenario'])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("APモデルを生成", type="primary"):
            st.session_state.conversation_step = 6
            st.rerun()
    with col2:
        if st.button("最初からやり直し"):
            # Reset all states
            for key in ['conversation_step', 'user_inputs', 'wikipedia_candidates', 
                       'selected_topic', 'selected_content', 'ap_history', 
                       'descriptions', 'story', 'generating']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

elif st.session_state.conversation_step == 6:
    if not st.session_state.generating:
        st.session_state.generating = True
        
        # Create imagination string
        imagination = f"【発展方向】{st.session_state.user_inputs['direction']}。【未来のビジョン】{st.session_state.user_inputs['vision']}。【個人的なシナリオ】{st.session_state.user_inputs['scenario']}"
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        ap_history = []
        descriptions = []
        
        try:
            # Stage 1: Wikipedia-based analysis
            status_text.text("第1段階：現実に基づくAPモデルを構築中...")
            progress_bar.progress(0.1)
            
            introduction = create_introduction_from_content(st.session_state.selected_topic, st.session_state.selected_content)
            descriptions.append(introduction)
            progress_bar.progress(0.2)
            
            ap_model = analyze_content_with_gpt(st.session_state.selected_topic, st.session_state.selected_content)
            ap_history.append({"stage": 1, "ap_model": ap_model})
            progress_bar.progress(0.3)
            
            # Stage 2: Future evolution
            status_text.text("第2段階：未来展望に基づくAPモデルを構築中...")
            
            introduction2, tech_resources2, daily_experience2 = update_to_next_stage(
                st.session_state.selected_topic, ap_history, descriptions, imagination, 2
            )
            descriptions.append(introduction2)
            progress_bar.progress(0.45)
            
            ap_model2 = update_ap_model(st.session_state.selected_topic, ap_history, descriptions, tech_resources2, daily_experience2, 2)
            ap_history.append({"stage": 2, "ap_model": ap_model2})
            progress_bar.progress(0.6)
            
            # Stage 3: Maturity stage
            status_text.text("第3段階：成熟期APモデルを構築中...")
            
            introduction3, tech_resources3, daily_experience3 = update_to_next_stage(
                st.session_state.selected_topic, ap_history, descriptions, imagination, 3
            )
            descriptions.append(introduction3)
            progress_bar.progress(0.75)
            
            ap_model3 = update_ap_model(st.session_state.selected_topic, ap_history, descriptions, tech_resources3, daily_experience3, 3)
            ap_history.append({"stage": 3, "ap_model": ap_model3})
            progress_bar.progress(0.85)
            
            # Generate story
            status_text.text("SF短編小説を生成中...")
            story = generate_story(st.session_state.selected_topic, ap_history, descriptions)
            progress_bar.progress(1.0)
            
            # Store results
            st.session_state.ap_history = ap_history
            st.session_state.descriptions = descriptions
            st.session_state.story = story
            st.session_state.generating = False
            
            status_text.text("✅ 生成完了！")
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            st.session_state.conversation_step = 7
            st.rerun()
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.session_state.generating = False

elif st.session_state.conversation_step == 7:
    st.subheader("🎉 生成結果")
    
    # Display evolution stages
    st.markdown("### 📈 進化段階")
    
    stages = ["第1段階：揺籃期", "第2段階：離陸期", "第3段階：成熟期"]
    
    for i, stage_name in enumerate(stages):
        with st.expander(stage_name, expanded=(i == 0)):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**説明:**")
                st.markdown(st.session_state.descriptions[i])
            with col2:
                st.markdown("**APモデル要素数:**")
                model = st.session_state.ap_history[i]["ap_model"]
                st.markdown(f"- 対象数: {len(model['nodes'])}/6")
                st.markdown(f"- 射数: {len(model['arrows'])}/12")
    
    # Display story
    st.markdown("### 📚 生成されたSF短編小説")
    with st.expander("SF小説を表示", expanded=True):
        st.markdown(st.session_state.story)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔎 APモデルを可視化", type="primary"):
            st.session_state.page = "visualization"
            st.rerun()
    
    with col2:
        # Download options
        ap_json = json.dumps(st.session_state.ap_history, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 APモデルJSONをダウンロード",
            data=ap_json,
            file_name="ap_model.json",
            mime="application/json"
        )
    
    with col3:
        st.download_button(
            label="📥 SF小説をダウンロード",
            data=st.session_state.story,
            file_name="sf_story.txt",
            mime="text/plain"
        )
    
    # Reset button
    st.markdown("---")
    if st.button("🔄 新しい物語を生成", type="secondary"):
        # Reset all states
        for key in ['conversation_step', 'user_inputs', 'wikipedia_candidates', 
                   'selected_topic', 'selected_content', 'ap_history', 
                   'descriptions', 'story', 'generating']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Sidebar information
with st.sidebar:
    st.header("📖 APモデルについて")
    st.markdown("""
    **アーキオロジカル・プロトタイピング（AP）モデル**は、社会文化を18の要素（6つの対象と12の射）で分析するモデルです。
    
    **Sカーブ進化モデル**:
    - **第1段階（揺籃期）**: 既存問題の解決と改善
    - **第2段階（離陸期）**: 急速な技術発展
    - **第3段階（成熟期）**: 安定した成熟状態
    """)
    
    if st.session_state.conversation_step > 0:
        st.markdown("---")
        st.markdown("**現在の進行状況:**")
        steps = [
            "興味の入力",
            "テーマ選択", 
            "発展方向",
            "未来ビジョン",
            "個人シナリオ",
            "内容確認",
            "APモデル生成",
            "結果表示"
        ]
        
        for i, step in enumerate(steps):
            if i < st.session_state.conversation_step:
                st.markdown(f"✅ {step}")
            elif i == st.session_state.conversation_step:
                st.markdown(f"🔄 {step}")
            else:
                st.markdown(f"⭕ {step}")

st.sidebar.markdown("---")
st.sidebar.markdown("Made by Zhang Menghan using Streamlit")