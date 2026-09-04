```turtle
pat:kr_1020210110925  a  ont:Patent, ont:RejectedPatent ;
    ont:filingDate          "2021-08-23"^^xsd:date ;
    ont:realizesProcess     <…/process/etch> ;
    ont:rejectedFor         ont:Rejection_Inventiveness ;
    ont:hasPriorArtExaminer <…/patent/kr_KR1020140023210A> .
<…/process/etch>          ont:hasSubprocess <…/subprocess/plasma_etch> .
<…/subprocess/plasma_etch>    ont:requiresSkill <…/skill/endpoint_detection> .
<…/expert/EXP_013>        ont:hasSkill      <…/skill/endpoint_detection> .
```
