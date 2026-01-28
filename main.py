from core.run import RunProgram

run = RunProgram()


def main() -> None:
    try:
        run.logger.info("stream active: True")  # заглушка
        run.create_wrapped_threads()
        run.logger.info("stream active: False")  # заглушка
    except Exception as e:
        print(f'The check returned an error: {e} Press Enter to finish.')


if __name__ == '__main__':
    main()
