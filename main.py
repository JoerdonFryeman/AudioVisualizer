from core.run import RunProgram

run = RunProgram()


def main() -> None:
    try:
        run.start_stream()
        run.create_wrapped_threads()
        run.stop_stream()
    except Exception as e:
        main_error_message = f'The check returned an error: {e}'
        run.logger.error(main_error_message)
        print(main_error_message)


if __name__ == '__main__':
    main()
