PREFIX = """
PREFIX : <http://www.semanticweb.org/ibrah/ontologies/2025/11/emotion-ontology#>
"""

GET_EMOTIONAL_STATES = PREFIX + """
SELECT DISTINCT ?state
WHERE {
  :text_1 :hasEmotionalState ?state .
}
"""

GET_INFERRED_GENRES = PREFIX + """
SELECT DISTINCT ?genre
WHERE {
  :text_1 :suggestsGenre ?genre .
}
"""

GET_BASE_EMOTIONS = PREFIX + """
SELECT DISTINCT ?emotion
WHERE {
  :text_1 :expressesEmotion ?emotion .
}
"""

GET_FULL_TRACE = PREFIX + """
SELECT DISTINCT ?emotion ?state ?genre
WHERE {
  OPTIONAL { :text_1 :expressesEmotion ?emotion . }
  OPTIONAL { :text_1 :hasEmotionalState ?state . }
  OPTIONAL { :text_1 :suggestsGenre ?genre . }
}
"""