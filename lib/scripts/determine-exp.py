import spack.environment as ev


def main():
    x = ev.active_environment()
    y = list(x.concrete_roots())
    # There may be multiple roots in the env. Assume that the experiment of
    # interest is the largest dag (every other root should just be an attempt
    # to constrain dependencies of this experiment).
    z = max(y, key=lambda i: sum(1 for _ in i.traverse()))
    print(z.name)


if __name__ == "__main__":
    main()
