on this page...

- [Purpose](#purpose)
- [Features](#features)
- [Languages & packages](#languages--packages)
- [Notes](#working-notes)

---

# Purpose

Periodically in my work I recognize that some process could be performed asynchronously. I have, on occasions, created asynchronous code, but not often enough to remember the structure/syntax. 

So there's an overhead to finding the project in which I used async code, then finding where in the project I used it, and then refamiliarizing myself with it (mentally separating the generalized async flow from the specific project-code). Additionally, it may be that the project/code I've found doesn't do a particular thing that I want to do in my active project (I'll know I've done the thing, but it's in a _different_ project I then need to find). 

Too often, with being busy the norm, that friction is enough to quash the desire to implement async code. Given this, I thought it'd be useful to create a template -- dummy but working code -- to quickly grok the aysnc structure and syntax for whatever project I'm working on.

---

# Languages & packages

Python is my primary language, and based on a fantastic article by Nathaniel Smith, "[Notes on structured concurrency...][NT.]", I'm using his "[trio][TR.]" library for the python async code.

[NT.]: <https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/> "article"
[TR.]: <https://github.com/python-trio/trio> "trio"

I'll also, in this repo, have code for [Rust][RU.]. I experiment with Rust for side-projects. Rust is challenging for me, but I love it. Any grappling with Rust makes me a better programmer overall — aside from the fact that I find that doing nearly any task in a second language makes me a better programmer, because I become more aware of the overall concept of a task, rather than simply its implementation. For Rust, I'm using the async library [tokio][TO.].

[RU.]: <https://www.rust-lang.org/> "Rust"
[TO.]: <https://tokio.rs/> "tokio"

---

# Features

For both the python and rust code, the flow will be to set up a queue of jobs, and have the jobs perform asynchronously. Each job will do some work, and save the data to both a memory structure and a file. The code will demonstrate three features:

- The first is the ability for each job to write to a shared memory-space. This would be useful if, for example, the task being performed (by a queue of asynchronous jobs) was preparing data for subsequent code.

- The second feature is a constraint on the number of jobs that can be performed concurrently. The would be useful to respect either external-constraints (ie rate-limiting when calling an API) or internal-constraints (ie CPU load or memory constraints).

- The third feature is the constraint that all file-updates must be done synchronously. This would be useful if there is some aspect of a task that must be done synchronously, but the rest of the task can be done asynchronously.

Not all work would require all features. But it'll be nice to have them all in one place for reference.

---


# Working notes

_(since I work on this as a side-project, I'll keep notes here to keep track of what I need to do next.)_

## next...

- write up this readme.
- figure out where to put "Usage" instructions (ie sourcing the py venv or the rust env settings file)
- maybe add a dummy env-settings file.
- now that I have a better idea of what I want to do, go back and update the python code to match what I want to do in rust.
- create the file that will be written to synchronously.
- set up dummy architecture to create a queue of jobs, limited by a capacitor/semaphore number.
- have each job do some work (initially a simply delay of seconds, but later a call to httpbin) -- and then write the results to the backup file synchronously.
- dockerize for super-easy setup.


## done...

- implement the python code.
- build out make_urls()
    - print the type of the initial random number.
    - move the random number maker to a lib.rs function.
    - move the results-dict-initializer to a lib.rs function.
    - start trying to update the results-dict.
    - convert the four-character numeral to a float.
    - add the float to the httpbin url-day.
    - store the httpbin url to the results-dict as a json-string.
    - revise hashmap to hold another hashmap.
    - redo update urls now that we have a hashmap of hashmaps.
        - I've build the new url, next to figure out how to update the hashmap.
- move make_urls() to lib.rs.

---
