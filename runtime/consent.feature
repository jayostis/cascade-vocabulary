Feature: Consent tiers
  What a model may do with a person's pods, and what the person must say first: a runtime or an app offers a model
  tools, and each tool takes one kind of act, at that kind's consent tier. The tools themselves, their names and their
  inputs, are each runtime's own.

  Each pod starts empty, at https://pod.example/, with Ada as its subject (scripted-input/people.ttl).

  Rule: Y1. Each tool a runtime offers a model takes one kind of act and runs at that kind's tier, free or ask
    decisions/consent-tiers.md, rows "kind of act", "a tool's tier" and "never".
    The kinds are cascade:ModelToolActKinds in ontologies/cascade.ttl, each with its cascade:consentTier. A tool
    declares the one kind it takes and its tier, by the tier's skos:notation, and the tier is its kind's. No tool takes
    a kind whose tier is cascade:ConsentTierNever, so no door offers one, whatever the person says. A runtime that
    offers no tool offers nothing to consent to, and passes.

    Example: no tool the runtime offers a model runs at a tier other than its kind's, or takes a kind whose tier is never
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the tools offered a model are listed
      When the query is:
        """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT DISTINCT ?tool WHERE {
          GRAPH <urn:cascade:tools> { ?tool rdfs:label ?name }
          FILTER (NOT EXISTS {
            GRAPH <urn:cascade:tools> { ?tool cascade:modelToolActKind ?kind ; cascade:consentTier ?tier }
            GRAPH <urn:cascade:vocabulary> { ?kind skos:inScheme cascade:ModelToolActKinds ; cascade:consentTier ?tier }
            FILTER (?tier != cascade:ConsentTierNever)
          } || EXISTS {
            GRAPH <urn:cascade:tools> { ?tool ?declares ?one , ?other }
            FILTER (?declares IN (cascade:modelToolActKind, cascade:consentTier) && ?one != ?other)
          })
        }
        """
      Then it answers nothing

  Rule: Y2. A tool at ask does nothing until the person says yes to that call
    decisions/consent-tiers.md, rows "ask" and "a door that cannot ask".
    The door that offers the tool shows the person what this call will do, and runs it only once they say yes to it.
    A no, or a question dismissed or left unanswered, does nothing. A yes is for the one call it answers. A door that
    cannot ask the person offers no tool at cascade:ConsentTierAsk.

    No example shows this rule yet: the reference runtime offers no tool at cascade:ConsentTierAsk. The first, and this
    rule's examples, come with jayostis/cascade-runtime-js#758.
