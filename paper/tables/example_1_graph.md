```turtle
pat:1020130000004  a  ont:Patent, ont:RejectedPatent ;
    skos:prefLabel          "플라즈마 식각 종점 검출 방법"@ko ;
    ont:filingDate          "2013-05-10"^^xsd:date ;
    ont:realizesProcess     <…/subprocess/plasma_etch> ;
    ont:rejectedFor         ont:Rejection_Inventiveness ;
    ont:hasPriorArtExaminer <…/patent/us_US7000001> .
<…/subprocess/plasma_etch>  ont:requiresSkill <…/skill/endpoint_detection> .
<…/expert/EXP_M01>          ont:hasSkill      <…/skill/endpoint_detection> .
```
