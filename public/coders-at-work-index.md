---
title: Coders at Work 全15人インデックス — プログラミングの巨人たちへのインタビュー集
tags:
  - python
  - devtools
  - cli
  - productivity
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---


## Coders at Work とは


Peter Seibel著（2009年刊）。プログラミングの歴史を作った15人への長編インタビュー集。各章は一人のプログラマーとの対話で構成され、プログラミングを始めたきっかけ、デバッグの手法、設計哲学、キャリアの転機などが語られる。600ページ超の大著だが、各章は独立しているので興味のある人物から読める。


## Ch.1 Jamie Zawinski（48ページ）


Lisp hacker / Netscape初期開発者 / ナイトクラブオーナー。

10代でCarnegie MellonのAIラボでLispを書き始める。Lucid社でXEmacsの開発を経てNetscapeに参加し、Unix版ブラウザとメールクライアントを開発。1998年にmozilla.orgの立ち上げを主導するも、進捗の遅さに幻滅して1年で離脱。その後サンフランシスコでDNA Loungeというナイトクラブを購入・経営するという異色の転身を遂げた。

話題: C++への嫌悪、数百万人にソフトを使われる喜びと責任、独学でプログラミングを学ぶことの意味。


## Ch.2 Brad Fitzpatrick（42ページ）


LiveJournal / memcached / MogileFS / Perlbal 作者。

1980年生まれで本書最年少。5歳で父親の自作Apple IIクローンでプログラミングを始めた。高校時代にLiveJournalを一人で開発し、大学在学中にユーザー数急増によるスケールの壁に直面。その過程でmemcachedをはじめとする複数のOSSインフラツールを生み出した。ソロ開発者がプロダクトを成長させていく過程のリアルな記録。

話題: 一人プロジェクトのスケーリング、他人のコードを読む恐怖の克服、Perl/Cでの実装判断。


## Ch.3 Douglas Crockford（42ページ）


JSON発明者 / Yahoo! JavaScript Architect。

元々はTV放送を専攻していたが、スタジオの時間が取れずFortranの授業を取ったのがプログラミングとの出会い。Atari、Lucasfilm、Electric Communitiesを経てYahoo!へ。XMLが複雑すぎると感じ、JavaScriptのオブジェクトリテラル記法からJSONを「発見」した（発明ではなく、既にあるものに名前をつけた、と本人は言う）。「JavaScript: The Good Parts」著者。ES4の複雑化に反対しES3.1（後のES5）を推進した。

話題: サブセッティング（良い部分だけ使う）による複雑性管理、コードリーディングの重要性。


## Ch.4 Brendan Eich（34ページ）


JavaScript作者 / Mozilla CTO。

Santa Clara大学で物理学を専攻し、C/アセンブリでの低レベルプログラミングから入って形式言語理論に惹かれる。Silicon Graphics、MicroUnityを経てNetscapeへ。極度の時間的プレッシャー（10日間）の中でJavaScriptを設計した。1998年にZawinskiと共にNetscapeのオープンソース化を主導し、mozilla.orgのチーフアーキテクトに。TraceMonkey JIT VMの開発にも関与。

話題: 10日で言語を作った経緯と政治的妥協、理想vs現実、静的コード解析の必要性。


## Ch.5 Joshua Bloch（38ページ）


Java Collections Framework設計者 / Google Chief Java Architect。

父親がBrookhaven国立研究所の化学者で、4年生の時にFortranに触れる。Columbia大学BS、Carnegie-Mellon大学PhD。Sun MicrosystemsでJava Collections Frameworkを設計・実装し、Java 5のいくつかの言語機能追加にも関与。「Effective Java」「Java Puzzlers」の著者で、API設計を「プログラミングそのもの」と捉える姿勢が一貫している。

話題: 良いAPI設計とは何か、Javaは複雑になりすぎたか、プログラミング言語の選択はバー選びに似ている。


## Ch.6 Joe Armstrong（36ページ）


Erlang作者 / Open Telecom Platform (OTP) 設計者。

1950年生まれ。元は物理学者で、PhD資金が尽きてCS転向。Donald Michie（英国AI研究の創設者の一人）のラボでAIとロボティクスに触れた後、AI予算凍結を受けてEricsson CS Labへ。電話交換機の高可用性要件（99.9999999%）からErlangを設計。ルーツはPrologにあり、並行処理に特化した言語として独自の進化を遂げた。

話題: 問題を解くための必要最小限のものを作る思想、並行性の本質、ブラックボックスを開けて中を理解する重要性。


## Ch.7 Simon Peyton Jones（46ページ）


Haskell設計者 / GHC (Glasgow Haskell Compiler) アーキテクト。

Microsoft Research Cambridge所属。1987年のHaskell定義プロジェクトの発起人の一人で、Haskell 98 Revised Reportを編集。PhDを持たない研究者・元教授という珍しい経歴。ストレージなし・メモリ100ワードのIBMスクール用コンピュータでプログラミングを始めた。関数型プログラミングを「壁にもう一つレンガを積むのではなく、まったく新しい壁を建てる」ラディカルなアプローチと見ている。

話題: 関数型の理論と実用性のバランス、Software Transactional Memory、異なる言語が生産性を変えるかの実証研究の難しさ。


## Ch.8 Peter Norvig（38ページ）


Google Research Director / AI実務家。

高校時代にPDP-8でBASICを始める。Googleの検索ログから3連続検索で俳句を作るプログラムを書いたり、世界最長の回文を生成したり、「Gettysburg Powerpoint Presentation」でPowerPointを風刺したりするハッカー気質の持ち主。NASA Ames Research Center、スタートアップJungleeを経てGoogleへ。

話題: ハッカー的アプローチvsエンジニア的アプローチ、設計技法の実際の価値、NASAは安価で信頼性の低いソフトの方がいいかもしれないという逆説。


## Ch.9 Guy Steele（48ページ）


Scheme共同発明者 / Common Lisp・Fortran・C・ECMAScript標準化委員。

「プログラミング言語の多言語話者」。真剣に使った言語はCOBOL, Fortran, APL, C, C++, Common Lisp, Scheme, Java, JavaScript, Haskell, TeXなど20以上。MITでSussmanと共に「The Lambda Papers」を執筆し、Schemeの原型を定義した。Jargon Fileの初期コンパイラでもある。言語を渡り歩いた「言語設計の生き字引」。

話題: ソフトウェア設計と文章執筆の関係、形式証明の価値と限界、言語間の思想的つながり。


## Ch.10 Dan Ingalls（40ページ）


Smalltalk主要実装者 / BitBlt発明者 / Xerox PARC。

Alan KayがSmalltalkの父なら、IngallsはSmalltalkの母。Kayの1ページのノートからSmalltalkの最初の実装（BASIC製）を作り、以降7世代のSmalltalkを実装した。元は物理学者でHarvardからStanfordへ進み、Don Knuthのプログラム計測の授業を受けた。PARCでBitBlt（ビットマップグラフィクス操作）を発明し、ポップアップメニュー等のGUI革新を可能にした。

話題: インタラクティブ開発環境の重要性、Lispを学ばなかった幸運、動的システムを作ってからロックダウンする方が良い。


## Ch.11 L. Peter Deutsch（36ページ）


12歳でLisp 1.5実装 / Ghostscript作者 / JIT発明の先駆者。

1950年代後半、11歳で父親がHarvardから持ち帰ったコードのメモに魅せられプログラミングを始める。14歳でMITのPDP-1上にLispを実装するという早熟な天才。UC BerkeleyでProject Genieのカーネルを書き、Xerox PARCでInterlisp、Smalltalk VMに取り組んでJITコンパイル技術の先駆者に。「分散コンピューティングの7つの誤謬」の著者。2002年にGhostscript開発を辞め、音楽作曲の勉強に転向。

話題: ポインタ/参照を持つ言語の根深い問題、ソフトウェアは資本資産でなく費用、プロとしてのプログラミングから引退した理由。技術者としてのキャリアの終わりを正直に語った珍しいインタビュー。


## Ch.12 Ken Thompson（36ページ）


UNIX共同発明者 / B言語作者 / UTF-8考案者 / チューリング賞(1983)。

小学校時代から2進数の算術に夢中。Bell LabsでMULTICSプロジェクトに参加した後、Bell Labsの撤退を機にDennis RitchieとともにUNIXを発明。Cの前身となるB言語も設計した。その後コンピュータチェスに興味を持ち、初の専用チェスコンピュータBelleを構築（当時最強）。Plan 9ではUTF-8 Unicodeエンコーディングを考案。

話題: エレクトロニクスへの愛、学生時代に教える側に回った型破りな経歴、「不要なものを削ぎ落とす」設計哲学、現代のプログラミングが怖い理由。


## Ch.13 Fran Allen（34ページ）


コンパイラ最適化パイオニア / 女性初チューリング賞受賞者(2006)。

数学教師志望だったが学生ローン返済のため1957年にIBM Researchに「一時的に」入社。最初の仕事はIBM科学者にFortranを教えること。結局IBM一筋45年。STRETCH-HARVESTコンパイラ、ACS-1スーパーコンピュータのコンパイラ、PTRANプロジェクト（Fortranの自動並列化）に取り組み、Static Single Assignment (SSA) 中間表現を開発した（現在の主要コンパイラで広く使用）。

話題: 1950年代の女性プログラマ事情、Cがコンピュータサイエンスに与えた害、コンピューティング分野の多様性。


## Ch.14 Bernie Cosell（46ページ）


ARPANET初期実装者 / BBN IMP開発チーム。

1969年、インターネットの前身ARPANETの最初の2ノードが接続された時、50kbpsの専用回線でパケットを送受信したInterface Message Processors (IMPs)のソフトウェアを書いた3人のうちの1人。Bolt Beranek and Newman (BBN)で26年間、タイムシェアリングシステムからARPANETまで幅広く従事。「マスターデバッガー」として社内で名を馳せ、問題プロジェクトに投入される「修理屋」役だった。

話題: マスターデバッガーとしての名声、明確なコードを書く重要性、IMPプロジェクトでバイナリパッチをやめさせた話。インターネットの「配管工」としての地道な視点。


## Ch.15 Donald Knuth（38ページ）


The Art of Computer Programming著者 / TeX作者 / チューリング賞(1974)。

アルゴリズム解析の父。1956年にCase Institute of Technologyの新入生としてIBM 650に出会い、マニュアルの10行プログラムを見て「改善できる」と思いのめり込む。Big-O記法の普及、LR構文解析の発明。1976年にTeXとMETAFONTの開発を開始（「1年で終わる」はずが10年に）。その過程で「文芸的プログラミング」を発明。1990年にメールの使用をやめ、「物事の上に立つ」のではなく「物事の底に至る」ことに専念。

話題: 文芸的プログラミングへの情熱、ブラックボックスへの両義的態度、再利用可能ソフトウェアの「過度な強調」への懸念。他の14人全員が「Knuthの本を読んだか」と聞かれる中、本人は飄々と自作を語る構成になっている。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/dev-tool/coders-at-work-index)*
