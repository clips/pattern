# -*- coding: utf-8 *-*
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import DBPedia

dbp = DBPedia()

# DBPedia is a database of structured information mined from Wikipedia.
# DBPedia data is stored as RDF triples: (subject, predicate, object),
# e.g., X is-a Actor, Y is-a Country, Z has-birthplace Country, ...
# If you know about pattern.graph (or graphs in general),
# this triple format should look familiar.

# DBPedia can be queried using SPARQL:
# http://dbpedia.org/sparql
# http://www.w3.org/TR/rdf-sparql-query/
# A SPARQL query yields rows that match all triples in the WHERE clause.
# A SPARQL query uses ?wildcards in triple subject/object to select fields.

# 1) Search DBPedia for actors.

# Variables are indicated with a "?" prefix.
# Variables will be bound to the corresponding part of each matched triple.
# The "a" is short for "is of the class".
# The "prefix" statement creates a shorthand for a given namespace.
# To see what semantic constraints are available in "dbo" (for example):
# http://dbpedia.org/ontology/
q = """
prefix dbo: <http://dbpedia.org/ontology/>
select ?actor where { 
    ?actor a dbo:Actor.
}
"""
for result in dbp.search(q, start=1, count=10):
    print(result.actor)
print("")

# You may notice that each Result.actor is of the form: 
# "http://dbpedia.org/resource/[NAME]"
# This kind of string is a subclass of unicode: DBPediaResource.
# DBPediaResource has a DBPediaResource.name property (see below).

# 2) Search DBPedia for actors and their place of birth.

q = """
prefix dbo: <http://dbpedia.org/ontology/>
select ?actor ?place where { 
    ?actor a dbo:Actor.
    ?actor dbo:birthPlace ?place.
}
order by ?actor
"""
for r in dbp.search(q, start=1, count=10):
    print("%s (%s)" % (r.actor.name, r.place.name))
print("")

# You will notice that the results now include duplicates,
# the same actor with a city name, and with a country name.
# We could refine ?place by including the following triple:
# "?place a dbo:Country."

# 3) Search DBPedia for actors born in 1970.

# Each result must match both triples, i.e.,
# X is an actor + X is born on Y.
# We don't want to filter by month and day (e.g., "1970-12-31"),
# so we use a regular expression instead with filter():
q = """
prefix dbo: <http://dbpedia.org/ontology/>
select ?actor ?date where { 
    ?actor a dbo:Actor.
    ?actor dbo:birthDate ?date. 
    filter(regex(str(?date), "1970-..-.."))
}
order by ?date
"""
for r in dbp.search(q, start=1, count=10):
    print("%s (%s)" % (r.actor.name, r.date))
print("")

# We could also make this query shorter,
# by combining the two ?actor triples into one:
# "?actor a dbo:Actor; dbo:birthDate ?date."

# 4) A more advanced example, in German:

q = """
prefix dbo: <http://dbpedia.org/ontology/>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select ?actor ?place where { 
    ?_actor a dbo:Actor.
    ?_actor dbo:birthPlace ?_place.
    ?_actor rdfs:label ?actor.
    ?_place rdfs:label ?place.
    filter(lang(?actor) = "de" && lang(?place) = "de")
}
order by ?actor
"""
for r in dbp.search(q, start=1, count=10):
    print("%s (%s)" % (r.actor, r.place))
print("")

# This extracts a German label for each matched DBPedia resource.
# - X is an actor,
# - X is born in Y,
# - X has a German label A,
# - Y has a German label B,
# - Retrieve A and B.

# For example, say one of the matched resources was:
# "<http://dbpedia.org/page/Erwin_Schrödinger>"
# If you open this URL in a browser,
# you will see all the available semantic properties and their values.
# One of the properties is "rdfs:label": a human-readable & multilingual label.

# 5) Find triples involving cats.

# <http://purl.org/dc/terms/subject>
# means: "is in the category of".
q = """
prefix dbo: <http://dbpedia.org/ontology/>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select ?cat ?relation ?concept where {
    ?cat <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:Felis>.
    ?cat ?_relation ?_concept.
    ?_relation rdfs:label ?relation.
    ?_concept rdfs:label ?concept.
    filter(lang(?relation) = "en" && lang(?concept) = "en")
} order by ?cat
"""
for r in dbp.search(q, start=1, count=10):
    print("%s ---%s--> %s" % (r.cat.name, r.relation.ljust(10, "-"), r.concept))
print("")

# 6) People whose first name includes "Édouard"

q = u"""
prefix dbo: <http://dbpedia.org/ontology/>
prefix foaf: <http://xmlns.com/foaf/0.1/>
select ?person ?name where { 
    ?person a dbo:Person.
    ?person foaf:givenName ?name.
    filter(regex(?name, "Édouard"))
}
"""
for result in dbp.search(q, start=1, count=10, cached=False):
    print("%s (%s)" % (result.person.name, result.name))
print("")
