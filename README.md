# HTN Planning for Minecraft

This project focuses on using Hierarchical Task Networks (HTNs) to solve construction problems in a Minecraft-style planning domain. By breaking down tasks into subtasks and applying heuristic-guided search, this planner can create various artifacts within specific resource and time constraints.

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [HTN Concepts](#htn-concepts)
  - [Operators](#operators)
  - [Methods](#methods)
  - [Heuristics](#heuristics)
- [Test Cases](#test-cases)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This project implements HTN planning for Minecraft-style tasks. HTNs break down tasks into smaller subtasks and decompose them until primitive actions can be applied to change the problem's state. The goal is to construct different artifacts using given resources within time constraints using Python's `pyhop` framework.

## Prerequisites

- Python 3.x
- Libraries: `pyhop` (included with the project)