# MVC Code Templates

Complete AdvPL/TLPP code templates for Protheus MVC screen generation. Use these as starting points and adapt to the specific table, fields, and business logic.

---

## Table of Contents

- [Template: Single Entity (Modelo 1)](#template-single-entity-modelo-1)
- [Template: Master-Detail (Modelo 3)](#template-master-detail-modelo-3)
- [Model Event Handlers](#model-event-handlers)
- [Master-Detail Validation and Commit Handlers](#master-detail-validation-and-commit-handlers)

---

## Template: Single Entity (Modelo 1)

A simple CRUD form for one table, with no grid (master-detail).

```tlpp
#include "tlpp-core.th"
#include "totvs.ch"
#include "fwmvcdef.ch"

Namespace company.module.feature

//===================================================================
// Main Function — Browse screen
//===================================================================
User Function MYMOD01()
  Local oBrowse as Object

  oBrowse := FWFormBrowse():New()
  oBrowse:SetAlias("ZZ1")
  oBrowse:SetDescription("My Custom Registration")
  oBrowse:AddLegend("ZZ1_STATUS == '1'", "GREEN", "Active")
  oBrowse:AddLegend("ZZ1_STATUS == '2'", "RED",   "Inactive")
  oBrowse:Activate()
Return

//===================================================================
// ModelDef — Business rules and data structure
//===================================================================
Static Function ModelDef() as Object
  Local oModel    as Object
  Local oStruct   as Object

  // Load structure from data dictionary (SX3)
  oStruct := FWFormStruct(1, "ZZ1")

  // Optional: Remove fields not managed by the model
  // oStruct:RemoveField("ZZ1_XFIELD")

  // Optional: Set field as non-editable
  // oStruct:SetProperty("ZZ1_STATUS", MODEL_FIELD_WHEN, FWBuildFeature(STRUCT_FEATURE_WHEN, ".F."))

  // Optional: Set initial value
  // oStruct:SetProperty("ZZ1_STATUS", MODEL_FIELD_INIT, FWBuildFeature(STRUCT_FEATURE_INIPAD, "'1'"))

  // Create the model