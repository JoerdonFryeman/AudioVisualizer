from core.run import RunProgram

run = RunProgram()


def main() -> None:
    try:
        run.create_wrapped_threads()
    except Exception as e:
        print(f'The check returned an error: {e} Press Enter to finish.')


if __name__ == '__main__':
    main()
