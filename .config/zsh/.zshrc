export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$XDG_CONFIG_HOME/local/share"
export XDG_CACHE_HOME="$XDG_CONFIG_HOME/cache"

export EDITOR="nano"
export VISUAL="nano"

export ZDOTDIR="$XDG_CONFIG_HOME/zsh"

export HISTFILE="$ZDOTDIR/.zhistory"    # History filepath
export HISTSIZE=10000                   # Maximum events for internal history
export SAVEHIST=10000                   # Maximum events in history file

source /home/abhinav/Experiments/.config/aliases

autoload -U compinit; compinit
_comp_options+=(globdots) # With hidden files
source /home/abhinav/Experiments/.config/completion.zsh

fpath=(/home/abhinav/Experiments/.config/ $fpath)
autoload -Uz prompt; prompt

setopt AUTO_PUSHD           # Push the current directory visited on the stack.
setopt PUSHD_IGNORE_DUPS    # Do not store duplicates in the stack.
setopt PUSHD_SILENT         # Do not print the directory stack after pushd or popd.

alias d='dirs -v'
for index ({1..9}) alias "$index"="cd +${index}"; unset index

source "/home/abhinav/Experiments/.config/cursor_mode"