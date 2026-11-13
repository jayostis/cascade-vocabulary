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
    decisions/consent-tiers.md, rows "ask" and "a door that cannot ask"; decisions/model-proposed-writes.md, row "asking".
    The door that offers the tool shows the person what this call will do, and runs it only once they say yes to it.
    A no, or a question dismissed or left unanswered, does nothing. A yes is for the one call it answers. A door that
    cannot ask the person offers no tool at cascade:ConsentTierAsk.

    Example: a no writes nothing
      Given a new pod for Ada on 2026-01-01 at 09:00
      When a model proposes "asthma" and Ada says no on 2026-01-02 at 09:00
      Then that step wrote no file

    Example: a question dismissed writes nothing
      Given a new pod for Ada on 2026-01-01 at 09:00
      When a model proposes "asthma" and Ada dismisses the question on 2026-01-02 at 09:00
      Then that step wrote no file

    Example: a question left unanswered writes nothing
      Given a new pod for Ada on 2026-01-01 at 09:00
      When a model proposes "asthma" and Ada leaves the question unanswered on 2026-01-02 at 09:00
      Then that step wrote no file

    Example: a yes is for the one call it answers, so the same proposal is asked again
      Given a new pod for Ada on 2026-01-01 at 09:00
      And a model proposes "asthma" and Ada says yes on 2026-01-02 at 09:00
      When a model proposes "asthma" and Ada says no on 2026-01-02 at 09:05 (asthma-again)
      Then that step wrote no file

    Example: a door that cannot ask offers no tool at ask
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the tools offered a model through a door that cannot ask are listed
      When the query is:
        """
        SELECT ?tool WHERE {
          GRAPH <urn:cascade:tools> { ?tool cascade:consentTier cascade:ConsentTierAsk }
        }
        """
      Then it answers nothing

  Rule: Y3. A write a model proposed names the model as its proposer, and the person who said yes
    decisions/model-proposed-writes.md, rows "where it is said", "the model", "the person who said yes", "a judgment's author", "told apart" and "when".
    The act that wrote it, an entry's session, the act that generated a judgment or a retraction, has one
    prov:qualifiedAssociation in cascade:ModelProposerRole, whose prov:agent is the model, a prov:SoftwareAgent named
    by an IRI and typed in the act's file, never the runtime; and one in cascade:PatientRole, whose prov:agent is the
    person who said yes. A judgment is prov:wasAttributedTo that person, and a retraction prov:wasAssociatedWith them,
    as the person's own are. Its time is the yes. A write the person makes themselves names no model, so a reader tells
    the two apart by the role alone.

    Example: an entry a model proposed names, on its session, the model and the person who said yes
      Given a new pod for Ada on 2026-01-01 at 09:00
      When a model proposes "asthma" and Ada says yes on 2026-01-02 at 09:00
      When the query is:
        """
        SELECT ?record ?started ?person ?proposedByAModel WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:asthma> prov:generated ?sessionFile , ?revisionFile }
          GRAPH ?sessionFile {
            ?session a cascade:HandEntrySession ; prov:startedAtTime ?started ;
              prov:qualifiedAssociation [ prov:hadRole cascade:PatientRole ; prov:agent ?person ] .
            OPTIONAL {
              ?session prov:qualifiedAssociation [ prov:hadRole cascade:ModelProposerRole ; prov:agent ?model ] .
              ?model a prov:SoftwareAgent
              FILTER NOT EXISTS { ?session prov:wasAssociatedWith ?model }
            }
          }
          GRAPH ?revisionFile { ?revision a cascade:Revision ; cascade:revisionOf ?record ; prov:wasGeneratedBy ?session }
          BIND (BOUND(?model) AS ?proposedByAModel)
        }
        """
      Then it answers:
        | record             | started                              | person                                    | proposedByAModel |
        | condition "Asthma" | "2026-01-02T09:00:00Z"^^xsd:dateTime | <https://pod.example/profile/card.ttl#me> | true             |

    Example: a judgment a model proposed is the person's and names the model, and one the person made names none
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And Ada files the judgment "latex-mango-different" on 2026-01-03 at 09:00
      When a model proposes "peanut-shellfish-different" and Ada says yes on 2026-01-04 at 09:00
      When the query is:
        """
        SELECT ?member ?author ?at ?proposedByAModel WHERE {
          GRAPH <urn:cascade:steps> { ?step prov:generated ?file }
          FILTER (?step IN (<urn:cascade:step:latex-mango-different>, <urn:cascade:step:peanut-shellfish-different>))
          GRAPH ?file {
            ?judgment a cascade:Judgment ; cascade:verdict cascade:Different ; prov:hadMember ?member ;
              prov:wasAttributedTo ?author ; prov:generatedAtTime ?at ; prov:wasGeneratedBy ?act .
            ?act prov:qualifiedAssociation [ prov:hadRole cascade:PatientRole ; prov:agent ?author ] .
            OPTIONAL {
              ?act prov:qualifiedAssociation [ prov:hadRole cascade:ModelProposerRole ; prov:agent ?model ] .
              ?model a prov:SoftwareAgent
            }
          }
          BIND (BOUND(?model) AS ?proposedByAModel)
        }
        """
      Then it answers:
        | member              | author                                    | at                                   | proposedByAModel |
        | allergy "Latex"     | <https://pod.example/profile/card.ttl#me> | "2026-01-03T09:00:00Z"^^xsd:dateTime | false            |
        | allergy "Mango"     | <https://pod.example/profile/card.ttl#me> | "2026-01-03T09:00:00Z"^^xsd:dateTime | false            |
        | allergy "Peanut"    | <https://pod.example/profile/card.ttl#me> | "2026-01-04T09:00:00Z"^^xsd:dateTime | true             |
        | allergy "Shellfish" | <https://pod.example/profile/card.ttl#me> | "2026-01-04T09:00:00Z"^^xsd:dateTime | true             |

    Example: a retraction a model proposed names, on itself, the model and the person who said yes
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And Ada files the judgment "latex-mango-different" on 2026-01-03 at 09:00
      When a model proposes "retract-latex-mango-different" and Ada says yes on 2026-01-04 at 09:00
      When the query is:
        """
        SELECT ?retracted ?person ?at ?proposedByAModel WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:retract-latex-mango-different> prov:generated ?file }
          GRAPH ?file {
            ?retraction prov:invalidated ?retracted ; prov:wasAssociatedWith ?person ; prov:startedAtTime ?at ;
              prov:qualifiedAssociation [ prov:hadRole cascade:PatientRole ; prov:agent ?person ] .
            OPTIONAL {
              ?retraction prov:qualifiedAssociation [ prov:hadRole cascade:ModelProposerRole ; prov:agent ?model ] .
              ?model a prov:SoftwareAgent
            }
          }
          BIND (BOUND(?model) AS ?proposedByAModel)
        }
        """
      Then it answers:
        | retracted                                       | person                                    | at                                   | proposedByAModel |
        | <urn:uuid:5e068021-5ff8-4580-8246-4f28453ace64> | <https://pod.example/profile/card.ttl#me> | "2026-01-04T09:00:00Z"^^xsd:dateTime | true             |
