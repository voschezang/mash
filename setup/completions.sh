_py_data_science_templates_main()
{
    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD-1]}

    # first arg: list of modules
    local options='echo linear_fit semilinear_fit fft random_walk'

    # second arg: module-specific arguments
    local echo='a few example terms'

    COMPREPLY=()
    case "$prev" in
        'echo')
            COMPREPLY=( $( compgen -W "$echo" -- $cur ) )
            ;;
        main|'./main')
            COMPREPLY=( $(compgen -W "$options" -- $cur ) )
            ;;
        *)
            # do nothing in case of undefined args
            ;;
    esac
}

_py_data_science_templates_main_simple()
{
    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD-1]}
    local options='linear_fit semilinear_fit fft random_walk'
    COMPREPLY=( $(compgen -W "$options" -- $cur ) );
}
