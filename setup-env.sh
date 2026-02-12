_this_file="${BASH_SOURCE[0]-${(%):-%N}-$0}"
_this_dir="$(CDPATH= cd -- "$(dirname -- "$_this_file")" 2>/dev/null && pwd -P)"

if [ -n "$PATH" ] && [ ":$PATH:" != "${PATH#:$_this_dir/bin:}" ]; then
  :  # already present
else
  PATH="$_this_dir/bin${PATH+:$PATH}"
  export PATH
fi