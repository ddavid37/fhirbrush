#!/bin/zsh

# Retrieve FHIR HAPI Sample Patient Data
url="http://hapi.fhir.org/baseR4/Patient?_format=json&_pretty=true"
curl -X GET "$url" -H "Accept: application/json" -o tmp/patient_response.json

#  Conditions, Observations, and MedicationRequests

url="http://hapi.fhir.org/baseR4/Observation?_format=json&_pretty=true"
curl -X GET "$url" -H "Accept: application/json" -o tmp/patient_observation.json


curl -X GET "http://hapi.fhir.org/baseR4/Condition?_format=json&_pretty=true" \
  -H "Accept: application/json"

curl -X GET "http://hapi.fhir.org/baseR4/Condition?patient=90128869&_format=json&_pretty=true" \
  -H "Accept: application/json"


  # Stage 1 through 5
curl -X GET "http://hapi.fhir.org/baseR4/Condition?code=http://snomed.info/sct|431855005,http://snomed.info/sct|431856006,http://snomed.info/sct|431857002,http://snomed.info/sct|431858007,http://snomed.info/sct|433146000,http://snomed.info/sct|709044004&_format=json&_pretty=true" \
  -H "Accept: application/json"