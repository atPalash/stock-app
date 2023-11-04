#!/bin/bash

_init_completions()
{
  local cur=${COMP_WORDS[COMP_CWORD]}
  COMPREPLY=( $(compgen -W "setEnv setPythonPackages makeDirs" -- $cur) )
}

complete -F _init_completions ./init.bash
