---
title: "Coders at Work — Index of All 15 Programmer Interviews"
date: 2026-03-14
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/coders-at-work-index"
devto_url: "https://dev.to/soytuber/coders-at-work-index-of-all-15-programmer-interviews-kcf"
devto_id: 3349948
---

■ What is Coders at Work?

Written by Peter Seibel (2009). A collection of long-form interviews with 15 programmers who shaped computing history. Each chapter is a conversation with one programmer, covering how they started programming, their debugging methods, design philosophy, and career turning points. At over 600 pages it is a substantial read, but each chapter stands alone — start with whoever interests you most.

■ Ch.1 Jamie Zawinski (48 pages)

Lisp hacker / early Netscape developer / nightclub owner.

Started writing Lisp at Carnegie Mellon's AI lab as a teenager. Worked at Lucid on XEmacs, then joined Netscape to build the Unix browser and mail client. Led the launch of mozilla.org in 1998 but left after a year, disillusioned by slow progress. Later bought and ran DNA Lounge, a nightclub in San Francisco.

Topics: hatred of C++, the joy and burden of having millions use your software, the value of being self-taught.

■ Ch.2 Brad Fitzpatrick (42 pages)

Creator of LiveJournal / memcached / MogileFS / Perlbal.

Born in 1980, the youngest person in the book. Started programming at age 5 on his father's homemade Apple II clone. Built LiveJournal in high school, then hit massive scaling challenges in college — which led him to create memcached and other OSS infrastructure tools. A real-world account of a solo developer growing a product.

Topics: scaling a one-person project, overcoming the fear of reading other people's code, making implementation decisions in Perl and C.

■ Ch.3 Douglas Crockford (42 pages)

Inventor of JSON / Yahoo! JavaScript Architect.

Originally studied TV broadcasting but couldn't get studio time, so took a Fortran class instead. Worked at Atari, Lucasfilm, and Electric Communities before joining Yahoo!. Found XML too complex and "discovered" JSON from JavaScript's existing object literal syntax (he insists he didn't invent it — just named what was already there). Author of "JavaScript: The Good Parts." Opposed the complexity of ES4 and championed ES3.1 (later ES5).

Topics: managing complexity through subsetting (using only the good parts), the importance of code reading.

■ Ch.4 Brendan Eich (34 pages)

Creator of JavaScript / Mozilla CTO.

Studied physics at Santa Clara University, entered programming through C and assembly, then became drawn to formal language theory. Worked at Silicon Graphics and MicroUnity before joining Netscape. Designed JavaScript under extreme time pressure — in just 10 days. Co-led the open-sourcing of Netscape in 1998 with Zawinski and became chief architect of mozilla.org. Also involved in the TraceMonkey JIT VM.

Topics: the story of creating a language in 10 days, political compromises in language design, ideals vs. reality, the need for static analysis.

■ Ch.5 Joshua Bloch (38 pages)

Designer of Java Collections Framework / Google Chief Java Architect.

His father was a chemist at Brookhaven National Laboratory, where Bloch encountered Fortran in fourth grade. BS from Columbia, PhD from Carnegie-Mellon. At Sun Microsystems, he designed and implemented the Java Collections Framework and contributed to several Java 5 language features. Author of "Effective Java" and "Java Puzzlers." Views API design as "programming itself."

Topics: what makes a good API, whether Java has become too complex, how choosing a programming language is like choosing a bar.

■ Ch.6 Joe Armstrong (36 pages)

Creator of Erlang / designer of Open Telecom Platform (OTP).

Born in 1950. Originally a physicist who switched to CS when his PhD funding ran out. Worked in Donald Michie's AI lab, then moved to Ericsson CS Lab after AI budgets were frozen. Designed Erlang to meet the extreme reliability requirements (99.9999999% uptime) of telephone switches. The language has its roots in Prolog and evolved as a specialized tool for concurrent programming.

Topics: building only the minimum needed to solve a problem, the essence of concurrency, the importance of opening black boxes to understand what is inside.

■ Ch.7 Simon Peyton Jones (46 pages)

Haskell designer / GHC (Glasgow Haskell Compiler) architect.

Based at Microsoft Research Cambridge. One of the founders of the Haskell project in 1987 and editor of the Haskell 98 Revised Report. Unusually, he has no PhD despite being a former professor and researcher. Started programming on an IBM school computer with no storage and only 100 words of memory. Sees functional programming as a "radical" approach — not adding another brick to the wall, but building an entirely new wall.

Topics: balancing theory and practicality in functional programming, Software Transactional Memory, the difficulty of empirically proving that different languages affect productivity.

■ Ch.8 Peter Norvig (38 pages)

Google Research Director / AI practitioner.

Started programming with BASIC on a PDP-8 in high school. Known for his hacker sensibility — he wrote a program to find haiku in Google search logs, generated the world's longest palindrome, and created the famous "Gettysburg Powerpoint Presentation" satirizing PowerPoint. Worked at NASA Ames Research Center and startup Junglee before joining Google.

Topics: hacker approach vs. engineer approach, the real value of design methodologies, the paradox that NASA might be better off with cheaper, less reliable software.

■ Ch.9 Guy Steele (48 pages)

Co-inventor of Scheme / standards committee member for Common Lisp, Fortran, C, and ECMAScript.

A "polyglot of programming languages" who has seriously used over 20 languages including COBOL, Fortran, APL, C, C++, Common Lisp, Scheme, Java, JavaScript, Haskell, and TeX. Co-authored "The Lambda Papers" with Sussman at MIT, defining the precursor to Scheme. Early compiler of the Jargon File. A living encyclopedia of language design who bridges theory and implementation.

Topics: the relationship between software design and writing prose, the value and limits of formal proofs, intellectual connections between programming languages.

■ Ch.10 Dan Ingalls (40 pages)

Principal implementor of Smalltalk / inventor of BitBlt / Xerox PARC.

If Alan Kay is the father of Smalltalk, Ingalls is its mother. He built the first Smalltalk implementation (in BASIC) from Kay's one-page notes and went on to implement seven generations of the language. Originally a physicist, he went from Harvard to Stanford where he took Don Knuth's program measurement class. At PARC, he invented BitBlt (bitmap graphics operations), enabling GUI innovations like pop-up menus.

Topics: the importance of interactive development environments, the luck of not learning Lisp first, building dynamic systems first and locking them down later.

■ Ch.11 L. Peter Deutsch (36 pages)

Implemented Lisp 1.5 at age 12 / creator of Ghostscript / JIT compilation pioneer.

In the late 1950s, at age 11, he became fascinated by code in memos his father brought home from Harvard's Cambridge Electron Accelerator. By 14 he had implemented Lisp on MIT's PDP-1. At UC Berkeley he wrote the kernel for Project Genie (early timesharing). At Xerox PARC he worked on Interlisp and Smalltalk VMs, pioneering JIT compilation. Author of the "Seven Fallacies of Distributed Computing." In 2002 he quit Ghostscript development to study music composition.

Topics: the deep problems with languages that have pointers/references, software as expense rather than capital asset, why he retired from professional programming. A rare honest account of the end of a career in technology.

■ Ch.12 Ken Thompson (36 pages)

Co-inventor of UNIX / creator of B language / designer of UTF-8 / Turing Award (1983).

Fascinated by binary arithmetic since elementary school. Joined the MULTICS project at Bell Labs, then co-invented UNIX with Dennis Ritchie after Bell Labs pulled out. Also designed B, the predecessor to C. Later turned to computer chess, building Belle — the first purpose-built chess computer (strongest of its era). On Plan 9, he designed UTF-8 Unicode encoding.

Topics: love of electronics, an unconventional path where the student became the teacher, a design philosophy of ruthlessly stripping away the unnecessary, why modern programming scares him.

■ Ch.13 Fran Allen (34 pages)

Pioneer of compiler optimization / first woman to receive the Turing Award (2006).

Wanted to be a math teacher but joined IBM Research in 1957 to pay off student loans — "temporarily." Her first assignment was teaching Fortran to IBM scientists. She stayed at IBM for 45 years. Worked on the STRETCH-HARVEST compiler, the ACS-1 supercomputer compiler, and the PTRAN project (automatic parallelization of Fortran). Developed the Static Single Assignment (SSA) intermediate representation, now widely used in modern compilers.

Topics: what it was like being a woman programmer in the 1950s, the harm C did to computer science, diversity in computing.

■ Ch.14 Bernie Cosell (46 pages)

Early ARPANET implementor / BBN IMP development team.

In 1969, when the first two nodes of ARPANET were connected, Cosell was one of three people who wrote the software for the Interface Message Processors (IMPs) that sent and received packets over 50kbps dedicated lines. Spent 26 years at Bolt Beranek and Newman (BBN) working on everything from timesharing systems to ARPANET. Known in-house as a "master debugger" — the fixer sent to rescue troubled projects. Also wrote a reimplementation of ELIZA (called DOCTOR) as a hobby, which spread across ARPANET.

Topics: his reputation as a master debugger, the importance of writing clear code, how he stopped the practice of binary patching on the IMP project. The perspective of the internet's "plumber" — someone who did unglamorous but essential work.

■ Ch.15 Donald Knuth (38 pages)

Author of The Art of Computer Programming / creator of TeX / Turing Award (1974).

The father of algorithm analysis. In 1956, as a freshman at the Case Institute of Technology, he encountered the IBM 650 and thought he could improve the 10-line program in the manual — and was hooked. Popularized Big-O notation, invented LR parsing. Started developing TeX and METAFONT in 1976 (expected to take one year, took ten). Invented "literate programming" in the process. In 1990 he stopped using email to focus on getting to "the bottom of things" rather than staying "on top of things."

Topics: his passion for literate programming, ambivalence toward black boxes, concerns about the "overemphasis" on reusable software. In a book where every other interviewee is asked "Did you read Knuth's books?", Knuth himself talks about his own work with characteristic nonchalance.
