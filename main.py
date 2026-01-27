from core.run import RunProgram

run = RunProgram()


def main() -> None:
    try:
        print("stream active: True")  # заглушка
        run.create_wrapped_threads()
        print("stream active: False")  # заглушка
    except Exception as e:
        print(f'The check returned an error: {e} Press Enter to finish.')


if __name__ == '__main__':
    main()
