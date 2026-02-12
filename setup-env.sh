if [ -n "${BASH_VERSION-}" ]; then
  _this_file=${BASH_SOURCE[0]}
elif [ -n "${ZSH_VERSION-}" ]; then
  eval '_this_file=${(%):-%N}'
else
  echo "This script must be sourced from bash or zsh." >&2
  return 1 2>/dev/null || exit 1
fi
# Get abspath
_this_dir="$(CDPATH= cd -- "$(dirname -- "$_this_file")" 2>/dev/null && pwd -P)"

case ":$PATH:" in
  *":$_this_dir/bin:"*)
    # already present: do nothing
    # This is an exact match, and e.g. won't match if PATH contains this
    # dir with a trailing slash after "bin". That's good enough to avoid
    # adding duplicate entries when re-sourcing this, but will add a
    # duplicate if the user manually added .../bin/ to their PATH
    :
    ;;
  *)
    PATH="$_this_dir/bin${PATH+:$PATH}"
    export PATH
    ;;
esac