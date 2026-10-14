"""Synthetic demo dataset generator.

IMPORTANT: this data is generated from templates so the project runs out of the box.
It is NOT real news - metrics on it say nothing about real-world performance.
Train on a real dataset (see README) for meaningful results.
"""
import random

import pandas as pd

POOLS = {
    "org": ["The finance ministry", "The central bank", "Health officials", "The city council",
            "Researchers at the state university", "The transport department",
            "The national statistics office", "A federal court", "The education department",
            "Company executives", "The environment agency", "The election commission"],
    "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "metric": ["unemployment", "consumer spending", "industrial output", "housing prices",
               "exports", "inflation", "hospital admissions", "school enrolment"],
    "moved": ["rose", "fell", "edged up", "declined"],
    "pct": ["0.8", "1.2", "2.4", "3.1", "4.3", "5.6"],
    "period": ["third quarter", "second quarter", "last fiscal year", "first half of the year"],
    "month": ["January", "March", "June", "September", "November"],
    "program": ["road maintenance programme", "vaccination campaign", "tax reform package",
                "housing subsidy scheme", "energy efficiency plan", "school funding formula"],
    "money": ["12", "45", "80", "150", "320"],
    "journal": ["a peer-reviewed medical journal", "the Journal of Applied Economics",
                "a national science review", "an academic policy journal"],
    "n": ["240", "1,200", "3,500", "18", "6"],
    "yrs": ["two", "three", "five", "ten"],
    "effect": ["improvement", "reduction in risk", "increase in output", "change in outcomes"],
    "caveat": ["the sample size was limited", "long-term effects remain unclear",
               "regional differences were significant", "the figures may be revised"],
    "votes": ["52", "61", "34", "77"],
    "votes2": ["40", "29", "45", "18"],
    "argument": ["the costs had not been fully explained", "smaller towns would be left behind",
                 "the timeline was unrealistic", "more public consultation was needed"],
    "group": ["The mainstream media", "Big pharma", "The elites", "Government insiders",
              "The global establishment", "Corrupt politicians"],
    "thing": ["the new vaccine", "the moon landing", "the economy report", "climate data",
              "the election results", "tap water", "5G towers"],
    "celebrity": ["A famous actor", "A top politician", "A billionaire", "A popular singer",
                  "A well-known TV host"],
    "conspiracy_act": ["poisoning the food supply", "rigging the vote count",
                       "hiding a cure for cancer", "spying on ordinary citizens",
                       "controlling the weather", "faking official statistics"],
    "ailment": ["diabetes", "back pain", "high blood pressure", "wrinkles", "belly fat"],
    "remedy": ["herbal tea", "kitchen spice", "ancient root", "secret fruit", "magic oil"],
    "conspiracy": ["the disaster was staged", "the results were secretly changed",
                   "the government knew all along", "the study was completely fabricated"],
    "scary_action": ["shut down the internet", "seize private savings",
                     "ban all cash", "cancel the next election"],
    "days": ["3", "5", "7", "10"],
}

REAL_SENT = [
    "{org} said on {day} that {metric} {moved} {pct} percent in the {period}, according to figures released this week.",
    "{org} announced a new {program} that will begin in {month}, with a budget of {money} million.",
    "In a statement, a spokesperson for {org} said the {program} would be reviewed after public consultation.",
    "The report, published in {journal}, analysed data from {n} participants over {yrs} years and found a modest {effect}.",
    "Officials said the decision follows a lengthy review and will take effect in {month}.",
    "Analysts said the results were broadly in line with expectations, though some cautioned that {caveat}.",
    "{org} declined to comment on the ongoing review, and no further details were released.",
    "The measure passed {votes} to {votes2} after several hours of debate, lawmakers said.",
    "Opposition members criticised the plan, arguing that {argument}.",
    "Independent experts said further research is needed before firm conclusions can be drawn.",
    "According to the report, {metric} {moved} {pct} percent compared with the same period a year earlier.",
    "The findings were presented at a conference on {day}, where researchers noted that {caveat}.",
    "A spokesperson said the {program} is expected to cost {money} million over {yrs} years.",
    "Local residents told reporters they welcomed the {program}, although some questioned how it would be funded.",
]

SENSATIONAL_REAL = [
    "Lawmakers reacted with outrage on {day} after {org} unveiled the {program}, in what critics called a shocking decision.",
    "The dramatic announcement stunned markets as {metric} {moved} {pct} percent, officials confirmed.",
    "Critics described the {program} as a disaster, but {org} defended it in a statement.",
]

FAKE_SENT = [
    "SHOCKING: {group} do NOT want you to know the truth about {thing}!!!",
    "You won't believe what {celebrity} secretly did - share this before it gets deleted!",
    "An anonymous insider reveals that {org} has been secretly {conspiracy_act} for years and the media is hiding it.",
    "Doctors are FURIOUS about this one weird trick that cures {ailment} in just {days} days.",
    "BREAKING: leaked documents PROVE that {conspiracy}. Wake up, people!",
    "They lied to you. {thing} is a hoax invented by {group} to control the population.",
    "This miracle {remedy} melts away {ailment} overnight and big pharma is desperate to ban it.",
    "Millions are outraged as {celebrity} is EXPOSED in a massive cover-up. The elites are terrified.",
    "Sources say {org} will soon {scary_action}, but nobody in the media dares to report it.",
    "Share this post if you agree. The truth is finally coming out and they cannot stop us now!",
    "Everything you were told about {thing} is a lie, and {group} are laughing at you.",
    "Nobody is talking about this, but {celebrity} just admitted that {conspiracy}!!!",
]

SUBTLE_FAKE = [
    "A source close to the matter, who asked not to be named, claimed that {org} has been secretly {conspiracy_act}.",
    "The claim could not be independently verified, but many people online believe {conspiracy}.",
    "Some say {thing} was never what {group} claimed, and insiders suggest the real story is being buried.",
    "It is widely believed that {celebrity} knew {conspiracy}, though no documents have been shown.",
]

DEBUNK_REAL = [
    "Officials dismissed online claims that {conspiracy} as a hoax, saying no evidence supports them.",
    "{org} said rumours about {thing} were false and urged the public to rely on official sources.",
    "Fact-checkers found that viral posts claiming {group} were {conspiracy_act} were misleading.",
]

FAKE_TITLES = [
    "SHOCKING truth about {thing} they are hiding from you",
    "{celebrity} EXPOSED: what {group} don't want you to see",
    "Doctors stunned by {remedy} that cures {ailment} fast",
    "BREAKING: proof that {conspiracy}",
    "Why {group} are lying about {thing}",
]
REAL_TITLES = [
    "{org} reports {metric} {moved} in {period}",
    "{org} to launch new {program} in {month}",
    "Study finds modest {effect}, researchers say",
    "Lawmakers approve {program} after debate",
    "{metric} {moved} {pct} percent, official data show",
]


class _Slots(dict):
    def __init__(self, rng):
        super().__init__()
        self.rng = rng

    def __missing__(self, key):
        return self.rng.choice(POOLS[key])


def _fill(template, rng):
    return template.format_map(_Slots(rng))


def generate(n=1200, seed=42, label_noise=0.04):
    """Return a DataFrame with columns title, text, label (FAKE/REAL).

    Classes deliberately overlap (calm-toned fakes, dramatic-sounding real news,
    real articles that debunk hoaxes) and a small share of labels is flipped, so
    the task is not trivially separable.
    """
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        fake = i % 2 == 0
        k = rng.randint(3, 6)
        if fake:
            r = rng.random()
            if r < 0.40:    # subtle, calm-toned fake news
                sents = rng.sample(SUBTLE_FAKE, 2) + rng.sample(REAL_SENT, 2)
            elif r < 0.70:  # fake claims mixed with normal reporting
                sents = rng.sample(FAKE_SENT, 2) + rng.sample(REAL_SENT, 2)
            else:           # loud, obvious fake news
                sents = rng.sample(FAKE_SENT, min(k, len(FAKE_SENT)))
            rng.shuffle(sents)
            title = _fill(rng.choice(FAKE_TITLES if rng.random() < 0.7 else REAL_TITLES), rng)
        else:
            sents = rng.sample(REAL_SENT, k)
            if rng.random() < 0.25:  # real news that sounds dramatic
                sents.append(rng.choice(SENSATIONAL_REAL))
            if rng.random() < 0.20:  # real news that debunks a hoax
                sents.append(rng.choice(DEBUNK_REAL))
            rng.shuffle(sents)
            title = _fill(rng.choice(REAL_TITLES if rng.random() < 0.85 else FAKE_TITLES), rng)
        text = " ".join(_fill(s, rng) for s in sents)
        is_fake_label = fake
        if rng.random() < label_noise:  # simulate ambiguous / mislabelled articles
            is_fake_label = not fake
        rows.append({"title": title, "text": text,
                     "label": "FAKE" if is_fake_label else "REAL"})
    return pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)
